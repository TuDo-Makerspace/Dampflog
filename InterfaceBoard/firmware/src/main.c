#include <stdio.h>

#include <stm8s.h>
#include <stm8s_it.h>

#include <msp49xx.h>
#include <midirx.h>
#include <delay_ms.h>

// DAC

#define CS_PORT GPIOC
#define CS_PIN GPIO_PIN_4

#define SCK_PORT GPIOC
#define SCK_PIN GPIO_PIN_5

#define MOSI_PORT GPIOC
#define MOSI_PIN GPIO_PIN_6

#define LDAC_PORT GPIOD
#define LDAC_PIN GPIO_PIN_2

#define MAX_DAC_VALUE 0x0FFF

// GATE

#define GATE_PORT GPIOC
#define GATE_PIN GPIO_PIN_3

#define OPEN_GATE() GPIO_WriteHigh(GATE_PORT, GATE_PIN)
#define CLOSE_GATE() GPIO_WriteLow(GATE_PORT, GATE_PIN)

// MIDI

#define UART_PORT GPIOD
#define UART_TX_PIN GPIO_PIN_5
#define UART_RX_PIN GPIO_PIN_6
#define UART_MIDI_BAUD 31250

#define SYSEX_MANUFACTURER_ID 0x7D // Manufacturer ID for private use

#define SYSEX_SET_DAC 0x01
#define SYSEX_SET_GATE 0x02

const mcp49xx_cfg cfg = {
    .dac = WRITE,
    .gain = DAC_GAIN_1X,
    .shutdown = DAC_ACTIVE,
    .buffer = DAC_BUF_ON,
};

void setup_gpios(void)
{
	GPIO_Init(CS_PORT, CS_PIN, GPIO_MODE_OUT_PP_HIGH_FAST);
	GPIO_Init(SCK_PORT, SCK_PIN, GPIO_MODE_OUT_PP_HIGH_FAST);
	GPIO_Init(MOSI_PORT, MOSI_PIN, GPIO_MODE_OUT_PP_HIGH_FAST);
	GPIO_Init(LDAC_PORT, LDAC_PIN, GPIO_MODE_OUT_PP_LOW_FAST); // Tie LDAC low since we only have one DAC.
	GPIO_Init(UART_PORT, UART_TX_PIN, GPIO_MODE_OUT_PP_HIGH_FAST);
	GPIO_Init(UART_PORT, UART_RX_PIN, GPIO_MODE_IN_PU_NO_IT);
	GPIO_Init(GATE_PORT, GATE_PIN, GPIO_MODE_OUT_PP_LOW_FAST);
}

void setup_clock(void)
{
	CLK_DeInit();
	CLK_HSECmd(DISABLE);
	CLK_LSICmd(DISABLE);
	CLK_HSICmd(ENABLE);

	while (CLK_GetFlagStatus(CLK_FLAG_HSIRDY) == FALSE)
		;

	CLK_ClockSwitchCmd(ENABLE);
	CLK_HSIPrescalerConfig(CLK_PRESCALER_HSIDIV1);
	CLK_SYSCLKConfig(CLK_PRESCALER_CPUDIV1);
	CLK_ClockSwitchConfig(CLK_SWITCHMODE_AUTO, CLK_SOURCE_HSI, DISABLE, CLK_CURRENTCLOCKSTATE_ENABLE);

	CLK_PeripheralClockConfig(CLK_PERIPHERAL_SPI, ENABLE);
	CLK_PeripheralClockConfig(CLK_PERIPHERAL_I2C, DISABLE);
	CLK_PeripheralClockConfig(CLK_PERIPHERAL_ADC, DISABLE);
	CLK_PeripheralClockConfig(CLK_PERIPHERAL_AWU, DISABLE);
	CLK_PeripheralClockConfig(CLK_PERIPHERAL_UART1, ENABLE);
	CLK_PeripheralClockConfig(CLK_PERIPHERAL_TIMER1, DISABLE);
	CLK_PeripheralClockConfig(CLK_PERIPHERAL_TIMER2, DISABLE);
	CLK_PeripheralClockConfig(CLK_PERIPHERAL_TIMER4, DISABLE);
}

void setup_spi(void)
{
	SPI_DeInit();
	SPI_Init(
	    SPI_FIRSTBIT_MSB,
	    SPI_BAUDRATEPRESCALER_2,
	    SPI_MODE_MASTER,
	    SPI_CLOCKPOLARITY_LOW,
	    SPI_CLOCKPHASE_1EDGE,
	    SPI_DATADIRECTION_1LINE_TX,
	    SPI_NSS_SOFT,
	    0x01); // > 0x00, else assertion will fail.
	SPI_Cmd(ENABLE);
}

void setup_uart(void)
{
	UART1_DeInit();
	UART1_Init(
	    UART_MIDI_BAUD,
	    UART1_WORDLENGTH_8D,
	    UART1_STOPBITS_1,
	    UART1_PARITY_NO,
	    UART1_SYNCMODE_CLOCK_DISABLE,
	    UART1_MODE_TXRX_ENABLE);
	UART1_ITConfig(UART1_IT_RXNE_OR, ENABLE);
	enableInterrupts();
	UART1_Cmd(ENABLE);
}

int putchar(int c)
{
	while (UART1_GetFlagStatus(UART1_FLAG_TXE) != SET)
		;
	UART1_SendData8(c);
	return c;
}

void spi_write16(uint16_t data)
{
	while (SPI_GetFlagStatus(SPI_FLAG_BSY))
		;
	GPIO_WriteLow(CS_PORT, CS_PIN);

	// Transmit MSB first.
	SPI_SendData(data >> 8);
	while (!SPI_GetFlagStatus(SPI_FLAG_TXE))
		;

	// Transmit LSB.
	SPI_SendData(data & 0xFF);
	while (!SPI_GetFlagStatus(SPI_FLAG_TXE))
		;

	GPIO_WriteHigh(CS_PORT, CS_PIN);
}

bool status_filter(midi_status_t status)
{
	// static bool sysex_started = false;

	// if (midirx_status_is_cmd(status, MIDI_STAT_SYSEX_END))
	// {
	// 	return sysex_started = false;
	// 	return true;
	// }

	// if (sysex_started)
	// 	return true;

	// if (midirx_status_is_cmd(status, MIDI_STAT_SYSEX))
	// {
	// 	sysex_started = true;
	// 	return true;
	// }

	// if (midirx_status_is_cmd(status, MIDI_STAT_NOTE_ON) ||
	//     midirx_status_is_cmd(status, MIDI_STAT_NOTE_OFF))
	// {
	// 	return true;
	// }

	// return false;

	return true;
}

void handle_midi_msg(midi_msg_t *msg)
{
	const midi_status_t status = msg->status;
	// const uint8_t ch = midirx_get_ch(status);

	if (midirx_status_is_cmd(status, MIDI_STAT_NOTE_ON))
	{
		OPEN_GATE();
	}
	else if (midirx_status_is_cmd(status, MIDI_STAT_NOTE_OFF))
	{
		CLOSE_GATE();
	}
}

void handle_sysex_msg(uint8_t *buf, size_t len)
{
	if (len < 2)
		return;

	uint8_t manufacturer_id = buf[0];
	uint8_t message_type = buf[1];

	if (manufacturer_id != SYSEX_MANUFACTURER_ID)
		return;

	switch (message_type)
	{
	case SYSEX_SET_DAC:
		if (len == 4)
		{
			uint16_t value = buf[2] << 8 | buf[3];
			spi_write16(mcp49xx_data(cfg, value));
			printf("Set DAC to %d\n", value);
		}
		break;
	case SYSEX_SET_GATE:
		if (len == 3)
		{
			uint8_t value = buf[2];
			if (value == 0x00)
			{
				CLOSE_GATE();
				printf("Closed gate\n");
			}
			else if (value == 0x01)
			{
				OPEN_GATE();
				printf("Opened gate\n");
			}
		}
		break;
	default:
		break;
	}
}

void main(void)
{
	midirx_set_status_filter(status_filter);
	midirx_on_midi_msg(handle_midi_msg);
	midirx_on_sysex_msg(handle_sysex_msg);

	setup_gpios();
	setup_clock();
	setup_spi();
	setup_uart();

	while (true)
		;
}

// See: https://community.st.com/s/question/0D50X00009XkhigSAB/what-is-the-purpose-of-define-usefullassert
#ifdef USE_FULL_ASSERT
void assert_failed(uint8_t *file, uint32_t line)
{
	while (TRUE)
	{
	}
}
#endif