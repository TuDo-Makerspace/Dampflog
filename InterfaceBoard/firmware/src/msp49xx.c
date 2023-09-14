#include <msp49xx.h>

mcp49xx_data_t mcp49xx_data(mcp49xx_cfg cfg, uint16_t value)
{
	uint16_t data = 0;
	data |= (cfg.dac << 15);
	data |= (cfg.buffer << 14);
	data |= (cfg.gain << 13);
	data |= (cfg.shutdown << 12);
	data |= (value & 0x0FFF); // Max 12 bits.

	return data;
}