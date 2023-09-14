#include <stm8s.h>
#include <stm8s_it.h>

#include <msp49xx.h>

#define CS_PORT GPIOC
#define CS_PIN GPIO_PIN_4

#define SCK_PORT GPIOC
#define SCK_PIN GPIO_PIN_5

#define MOSI_PORT GPIOC
#define MOSI_PIN GPIO_PIN_6

#define LDAC_PORT GPIOD
#define LDAC_PIN GPIO_PIN_2

void init_clock(void)
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
	CLK_PeripheralClockConfig(CLK_PERIPHERAL_UART1, DISABLE);
	CLK_PeripheralClockConfig(CLK_PERIPHERAL_TIMER1, DISABLE);
	CLK_PeripheralClockConfig(CLK_PERIPHERAL_TIMER2, DISABLE);
	CLK_PeripheralClockConfig(CLK_PERIPHERAL_TIMER4, DISABLE);
}

void init_spi(void)
{
	GPIO_Init(CS_PORT, CS_PIN, GPIO_MODE_OUT_PP_HIGH_FAST);
	GPIO_Init(SCK_PORT, SCK_PIN, GPIO_MODE_OUT_PP_HIGH_FAST);
	GPIO_Init(MOSI_PORT, MOSI_PIN, GPIO_MODE_OUT_PP_HIGH_FAST);

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

void spi_write16(uint16_t data)
{
	while (SPI_GetFlagStatus(SPI_FLAG_BSY))
		;
	GPIO_WriteLow(CS_PORT, CS_PIN);

	SPI_SendData(data >> 8); // MSB
	while (!SPI_GetFlagStatus(SPI_FLAG_TXE))
		;

	SPI_SendData(data & 0xFF); // LSB
	while (!SPI_GetFlagStatus(SPI_FLAG_TXE))
		;

	GPIO_WriteHigh(CS_PORT, CS_PIN);
}

const mcp49xx_cfg cfg = {
    .dac = WRITE,
    .gain = DAC_GAIN_1X,
    .shutdown = DAC_ACTIVE,
    .buffer = DAC_BUF_ON,
};

void main(void)
{
	init_clock();
	GPIO_Init(LDAC_PORT, LDAC_PIN, GPIO_MODE_OUT_PP_LOW_FAST); // Tie LDAC low since we only have one DAC.
	init_spi();

	uint16_t i = 0;
	while (1)
	{
		mcp49xx_data_t data = mcp49xx_data(cfg, i);
		spi_write16(data);
		for (uint16_t j = 0; j < 100; j++)
			;

		if (i < 4095)
			i++;
		else
			i = 0;
	}
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