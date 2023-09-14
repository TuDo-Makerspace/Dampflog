#ifndef _MSP49XX_H_INCLUDED
#define _MSP49XX_H_INCLUDED

#include <stdint.h>

typedef enum
{
	WRITE = 0,  // 49x1's
	IGNORE = 1, // 49x1's
	DAC_A = 0,  // 49x2's
	DAC_B = 1   // 49x2's
} DAC;

typedef DAC DAC_APPLY; // 49x1's only have one DAC, so the bit is interpreted as apply or ignore

typedef enum
{
	DAC_GAIN_1X = 1,
	DAC_GAIN_2X = 0
} DAC_GAIN;

typedef enum
{
	DAC_SHUTDOWN = 0,
	DAC_ACTIVE = 1
} DAC_SHDN;

typedef enum
{
	DAC_BUF_OFF = 0,
	DAC_BUF_ON = 1
} DAC_BUF;

typedef struct
{
	DAC dac;
	DAC_GAIN gain;
	DAC_SHDN shutdown;
	DAC_BUF buffer;
} mcp49xx_cfg;

typedef uint16_t mcp49xx_data_t;

mcp49xx_data_t mcp49xx_data(mcp49xx_cfg cfg, uint16_t value);

#endif