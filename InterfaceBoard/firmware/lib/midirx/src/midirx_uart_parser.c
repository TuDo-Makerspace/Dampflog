/*
 * Copyright (C) 2023 Patrick Pedersen

 * This program is free software: you can redistribute it and/or modify
 * it under the terms of the GNU General Public License as published by
 * the Free Software Foundation, either version 3 of the License, or
 * (at your option) any later version.

 * This program is distributed in the hope that it will be useful,
 * but WITHOUT ANY WARRANTY; without even the implied warranty of
 * MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
 * GNU General Public License for more details.

 * You should have received a copy of the GNU General Public License
 * along with this program.  If not, see <https://www.gnu.org/licenses/>.
 *
 * Description: Template main file for STM8S103F3P6 PlatformIO projects
 */

#include "midirx.h"
#include "midirx_uart_parser.h"
#include "midirx_msg.h"

typedef enum {
	STATUS,
	DATA1,
	DATA2
} midi_rx_state_t;

/**
 * @brief Calls callback functions after a MIDI message has been received
 * @param msg Pointer to a @ref midi_msg_t struct
 */
inline void on_rx_complete(midi_msg_t *msg)
{
	if (_midi_msg_callback == NULL)
		return;

	_midi_msg_callback(msg);
}

// See header file for documentation
void midirx_parse_uart_rx(uint8_t data)
{
	static midi_msg_t msg;
	static midi_rx_state_t state = STATUS;

	switch (state) {
	case STATUS:
		if (!midirx_is_status(data)) {
			return;
		}

		if (_midi_status_filter != NULL &&
		    !_midi_status_filter(data)) {
			return;
		}

		msg.status = data;
		state = DATA1;
		break;

	case DATA1:
		if (!midirx_is_data(data)) {
			state = STATUS;
			return;
		}

		msg.data1 = data;
		state = DATA2;
		break;

	case DATA2:
		if (!midirx_is_data(data)) {
			state = STATUS;
			return;
		}

		msg.data2 = data;
		state = STATUS;
		on_rx_complete(&msg);
		break;
	}
}