#include <stdio.h>
#include <stm8s.h>
#include <log.h>

int putchar(int c)
{
	while (UART1_GetFlagStatus(UART1_FLAG_TXE) != SET)
		;
	UART1_SendData8(c);
	return c;
}