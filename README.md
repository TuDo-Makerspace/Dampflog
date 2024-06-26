# Dampflog <!-- omit in toc -->

![Showcase](docs/Showcase.JPG)

A synthesizer built from an [old Conrad Train whistle PCB](docs/DLP_Manual.pdf)

> This project was created during the [TU-DO Makerspace's Makerthon #1](https://www.instagram.com/p/CwGRmoHKHiY/?igshid=MzRlODBiNWFlZA==)!

# Table Of Contents <!-- omit in toc -->
- ["Dampflockpfeife" - The Steam Locomotive Whistle](#dampflockpfeife---the-steam-locomotive-whistle)
	- [Product Description](#product-description)
	- [The Circuit](#the-circuit)
		- [1. Power stage](#1-power-stage)
		- [2. Trigger/Gate circuit](#2-triggergate-circuit)
		- [3. Oscillator](#3-oscillator)
		- [4. Output Stage/Amplifier](#4-output-stageamplifier)
- [Background - The Makerthon](#background---the-makerthon)
- [Hacking the PCB](#hacking-the-pcb)
	- [Power Input](#power-input)
	- [Audio Output](#audio-output)
	- [Original Controls](#original-controls)
	- [HOLD Switch](#hold-switch)
	- [Gate Input](#gate-input)
	- [Pitch Control](#pitch-control)
		- [Initial Approach](#initial-approach)
		- [Time to get serious](#time-to-get-serious)
		- [Screw CV, we're going full MIDI](#screw-cv-were-going-full-midi)
		- [A PCB to rule them all](#a-pcb-to-rule-them-all)
- [The Result](#the-result)
- [Future plans](#future-plans)


## "Dampflockpfeife" - The Steam Locomotive Whistle

![PCB](docs/PCBShowcase.jpg)

> Pardon the crude picture, I unfortunately didn't take any pictures of the PCB before I started hacking it.

### Product Description

The "Dampflockpfeife" is a [Printed Circuit Board that was published by Conrad Electronics in 1997 as a DIY soldering set for model train enthusiasts](docs/DLP_Manual.pdf). It attempts to mimic the sound of a steam locomotive whistle when activated. The circuit board is intended to be integrated into a model train track setup, where it can be activated in response to a passing train. To adjust the whistle sound, the PCB features two potentiometers — one for adjusting the pitch and another for setting the duration of the whistle blast. Activating the sound requires short-circuiting two contacts on the PCB, which can be achieved, for example, by employing a button or a sensor mechanism.

Here's a showcase of how the Whistle sounds:

https://github.com/TU-DO-Makerspace/Dampflog/assets/12089409/401a1205-c79d-425e-badc-b6d5c987373b

As you can hear, it does somewhat resemble a steam locomotive whistle, albeit rather poorly. That being said, a digital solution at the time would likely have been signficantly more expensive.

### The Circuit

Given its publication date, it should not come as a surprise that this circuit is devoid of any digital components. The whistle sound is synthesized entirely through analog means. Fortunately, the PCB's manual is, despite its age, [readily accessible online](docs/DLP_Manual.pdf). It offers a comprehensive resource, featuring a circuit description, a complete schematic, and even a PCB layout. While the manual is in German, fear not, as we will provide a comprehensive coverage of the circuit here.

Here's the schematic of the circuit:

![Schematic](docs/DLP_Schematic.png)

The circuit can be split into four parts:

- 1. Power stage
- 2. Trigger/Gate circuit
- 3. Oscillator
- 4. Output Stage/Amplifier

#### 1. Power stage

![Power stage](docs/DLP_Schematic_Power.png)

On the first glance we can recognize a full bridge rectifier, indicating that the Circuit takes AC as an input. I initially found it somewhat peculiar but as I later found out, this choice was made to ensure compatibility with "Märklin" model train tracks, which, in contrast to their competitors, rely on AC voltage. According to various sources, this voltage typically falls within the range of 16 to 24 volts. While I'm no expert in model trains, I did have the fortunate opportunity to recently talk with someone knowledgeable in the field. They explained me that this unique reliance on AC voltage is a rather quirky characteristic of Märklin model trains.

Now, returning to the circuit itself: As mentioned, the AC voltage first passes through a full bridge rectifier (D1-D4) to convert it into a pulsating DC signal. Subsequently, this signal is smoothed out by a 100uF capacitor (C12). The stabilized voltage is then further regulated down to a consistent 12 volts via a 7812 linear regulator (IC1). This 12-volt output is then used as the supply voltage to power the remaining components of the circuit.

For my intents and purposes the whole power section was not needed. Instead, I simply used a 12V DC power supply and connected it directly to the 12V rail.

#### 2. Trigger/Gate circuit

![Trigger Stage](docs/DLP_Schematic_Trigger.png)

As I delved into the schematic, one symbol immediately captured my attention: the NE555 timer IC. At first glance, I presumed it might be responsible for generating the whistle tone itself, but I quickly discovered that it operates in monostable/one-shot mode to generate a temporary gate signal. This gate signal serves to trigger the oscillator. Its duration is adjustable via potentiometer P2, allowing for a range spanning 1 to 10 seconds based on the potentiometer's setting.

To output a gate signal, a switch connected to the trigger input of the NE555 (labeled "Start" in the schematic) must be closed. This action pulls down the trigger pin and prompts the NE555 to produce a high signal at output pin 3, sustaining it for the preconfigured duration. This signal subsequently forward-biases transistor T3. Since the collector of T3 is connected to the base of T2, T2 becomes reverse-biased as a result. If no gate signal is present (default state), T2 is forward-biased via the pull-up resistor R4, which keeps the feedback path of the oscillator grounded, preventing it from generating any tone. With T2 in a reverse-biased state, the feedback path is no longer held down, enabling the oscillator to oscillate freely and synthesize the desired tone.

#### 3. Oscillator

![Oscillator](docs/DLP_Schematic_Oscillator.png)

The oscillator is arguably the most important part of the entire circuit. It somewhat resembles a relaxation oscillator built around an LM741 operational amplifier (OP-AMP), albeit with a distinct set of quirks that give it its unique character.

Firstly, the positive feedback loop takes an unusual turn as it's AC-coupled via capacitors C1 and C2. Further, what sets this oscillator apart and makes it particularly fascinating, is the inclusion of an NPN transistor, T1 within the feedback path. This transistor operates in a rather atypical diode configuration, with its emitter connected to the more positive rail. Its role? To introduce a subtle touch of chaos by injecting noise into the feedback path. But wait, there's more. The op-amp's output is also coupled to the "Offset Null" pin via capacitor C7, further contributing to the circuit's distinctive noisy sound. The noise injected into the feedback path causes subtle changes in the oscillator's frequency. This is precisely what gives this PCB its steam locomotive" sound. The rest of the circuit aligns more closely with a standard OP-AMP relaxation oscillator.

The frequency of this oscillator is adjustable through potentiometer P1, which defines the voltage propagated through the positive feedback pathway. On the inverting input of the OP-AMP, an RC circuit formed by R8 and C6 generates a triangular waveform. When P1's resistance decreases, the voltage in the positive feedback path decreases as well. Consequently, the triangular wave at the non-inverting input catches up to the inverting input faster, escalating the oscillator's frequency. When P1 reaches a low-enough resistance, the propagated voltage drops sufficiently low to stabilize the oscillation. In this state, only the eerie and somewhat spooky sound produced by the noise feedback path remains audible. You can listen to a recording of this peculiar sound [here](https://soundcloud.com/user-631734174/bc548-diode-configuration-noise).

An interesting side effect of this stabilization is that the oscillator experiences hysteriesys due to it's schmitt-trigger like positive feedback. As a result, P1 must be turned further back to retrigger the oscillation.

In total, the oscillator offers a frequency spectrum spanning approximately 116Hz (at infinite resistance) to 700Hz (at the point of stabilization). This equates to roughly 2.5 octaves of range, covering pitches from A#2 to F5.

Below are a couple of screenshots of LTSpice simulations to further illustrate the behaviour of the oscillator.

LT SPICE STUFF HERE

A crucial aspect of this circuit: The relationship between frequency and the potentiometer P1 follows an inversely multiplicative response. At lower resistances (corresponding to higher frequencies), even slight adjustments to P1 produce rapid frequency shifts. In contrast, at higher resistances (corresponding to lower frequencies), making similar changes to P1 yields only slight changes in frequency. Ideally, for precise pitch control, we would expect this behavior to be exponential, not inverse multiplicative. This characteristic became a significant challenge when attempting to implement 1V/Octave pitch control, as we will explore later.

![Frequency vs Resistance Response](docs/P1_FreqVSRes.png)

Additionally, the LM741 exhibits an intersting trait: At higher frequencies, it exhibits a low-pass filtering effect. Lower frequencies result in a more square-like output, while higher frequencies manifest as a more triangular waveform. This phenomenon can likely be attributed to the slew rate of the LM741, and it controbutes to a distinctive and appealing character to the resulting sound.

#### 4. Output Stage/Amplifier

![Output Stage](docs/DLP_Schematic_Output.png)

To be honest, I don't possess enough experience in the field of transistor amplifiers, and given that the output stage is not really relevant for my project, I haven't delved deeply into its functionality. I have a vague suspicion that T4 and T5 might play a role in amplifying the signal voltage, while the complementary push-pull amplifier comprising T7 and T6 might be responsible for current buffering. However, as mentioned, I'm not entirely certain so I welcome any corrections or clarifications if I'm off the mark.

## Background - The Makerthon

Before discussing the modifications I made to the circuit board, I'd like to provide some context for this project. This project was born out of a Hackathon organized at our Makerspace, called "Makerthon". The theme, albeit not mandatory, was to "Upcycle" old electronics that we had lying around in the Makerspace. The time frame for the Hackathon was about two and a half days.

<p align="center">
<img src="docs/MakerthonPoster.png" height=600px>
</p>

During the first day the task was to scavange for old electronics and brainstorm ideas for potential projects. After digging through an old box of PCBs I stumbled upon the Dampflog PCB. From there, it didn't take long to find the manual online and jump to the idea of turning this thing into a musical synthesizer!

## Hacking the PCB

After thoroughly examining the circuit, it was time to transform the PCB into a musical synthesizer. Before I could wield my trusty soldering iron, I needed to formulate a roadmap of the features I wanted to "hack" into the PCB. Here's my initial list of requirements:

- 12V DC Power Input
- 3.5mm Jack audio output with volume control
- A HOLD switch to permanently enable the gate signal
- A 0-5V Gate input to trigger the gate signal
- A 1V/Octave CV input to control the pitch

Beyond these additions, I wanted to ensure that the device retained its original functionality. To achieve this, I included a push-button for manual gate signal triggering, along with potentiometers to adjust the gate signal duration and pitch manually.

For housing the PCB, I repurposed an old metal box that had once contained a [data transfer switch (KVM Switch)](https://www.amazon.com/Kentek-Parallel-Peripherals-Devices-Printer/dp/B07KWRWLRN)—which we happened to have lying around in the makerspace. Typically, I would have opted for a 3D-printed enclosure, but as mentioned prior, this project was created during a Hackathon, and I simply didn't have the luxury of time for enclosure design and printing. As a playful touch, I even gave the enclosure a neat little spray-paint job, just for the fun of it.

### Power Input

Adding a 12V DC power input was rather trivial. I simply connected a 2.1mm DC barrel jack to the 12V rail of the PCB with a switch in between to turn the device on and off. I also added a small red power LED next to the Jack to indicate that the device is powered on.

<p align="center">
	<img src="docs/12V.png">
</p>

I tried to solder the power wires as close to the power stage as possible to maximize the utilization of the power capacitors on the PCB. The DC jack found its home on the front side of the enclosure, while the switch was thoughtfully situated on the back side.

In hindsight, I realize that it might have been more ergonomically advantageous to swap the positions of the jack and the switch.

PICTURE OF JACK HERE

### Audio Output

Adding audio output was also pretty straight forward. I simply connected a 3.5mm audio jack to the output of the amplifier. To provide volume control for the output signal, I introduced a potentiometer which serves as a voltage divider.

<p align="center">
	<img src="docs/AudioOut.png">
</p>

The potentiometer and jack were mounted on the front side of the enclosure for easy accessibility.

PICTURE OF AUDIO JACK HERE

It's important to know that the output can reach up to 10VPP, which is **NOT** suitable for headphones. I recommend only
using the device in combination with an audio interface or external amplifier. The volume should always be turned down first
before connecting the device to an audio interface or amplifier.

The advantage of such high peak-to-peak voltage is that it can be used to drive a speaker directly and can also interface easily with eurorack modules which also operate at similar voltage levels.

### Original Controls

As previously mentioned, it was essential to retain the device's original intended functionality. One addition was a green arcade-style push button mounted on the top side of the enclosure to serve as a trigger for the gate signal. I also mounted two potentiometers on the top side to control the duration of the gate signal and the pitch. It should be noted that I used a 200k pot instead the original inteded value of 50k. This modification expanded the available pitch range. A 50k pot couldn't quite reach the lower frequency limits of the oscillator.

PICTURE OF ORIGINAL CONTROLS HERE

### HOLD Switch

Incorporating a HOLD switch proved to be the first slightly more complicated addition to the circuit. After some consideration, I determined that a switch connected in parallel to transistor T3 would provide the most effective solution. When this switch is in the closed position, it essentially replicates the scenario where T3 is forward-biased. Consequently, this keeps T2 in a reverse-biased state, ensuring that the oscillator remains continually enabled.

<p align="center">
	<img src="docs/HOLD.png">
</p>

For user convenience, the HOLD switch has been mounted next to the trigger button.

PICTURE OF HOLD SWITCH HERE

### Gate Input

To introduce a GATE support, I drew inspiration from the design of the HOLD switch. I incorporated a 3.5mm jack, connected to an NMOS transistor positioned in parallel with T3. To guarantee that the MOSFET remains consistently off when the jack is not used, I added a 220k Pull-Down resistor at the gate.

Additionally, for added protection against accidental voltage spikes (e.g., during jack cable insertion), I integrated a 10k resistor between the jack tip and the MOSFET's gate. This arrangement effectively increases the RC constant (C being the MOSFETS capacitance), safeguarding the MOSFET from potential damage.

<p align="center">
	<img src="docs/GATE.png">
</p>

PICTURE OF GATE JACK HERE

Without revealing too much ahead, I made some slight modifications to the GATE input during the course of the project. More on that later.

To put the GATE support to the test, I connected my trusyworthy Arturia Keystep to the GATE input, only to discover that the oscillator isn't particularly well-suited for GATE input, at least not in the traditional sense. You see, the oscillator exhibits a slight attack duration and a rather brief decay time. This means it requires a significant amount of time to reach its intended pitch but quickly ceases once the GATE signal drops. Consequently, rapid GATE signals fail to give the oscillator adequate time to achieve its intended pitch, resulting in a "chopped" tone. This behavior is primarily attributed to the fact that the oscillator relies on RC circuits, which are intentionally designed to take time to charge up.

Despite this, I still found the GATE input to be genuinely useful in only two scenarios:

- When the BPM/tempo setting allows the oscillator sufficient time to attain its desired pitch.
- When creating a percussive, choppy sound effect.

Interestingly, I found the second scenario to be a seriously cool unintended feature. It particularly shines when the oscillator is pushed to its upper limits, allowing only the noise within the feedback path to be gated. This makes for a dirty, industrial screechy sound which is great for harsher techno tracks. You can explore a sample of this distinctive sound, enhanced with a touch of distortion, reverb, flanging, and some percussion, by [clicking here](https://soundcloud.com/user-631734174/dampflog-gate-noise-test).

### Pitch Control

#### Initial Approach

To at least deliver a proof of concept for the end of the Makerthon I had to at least implement some form of half-arsed pitch control. For the sake of demonstration I
disattached the Pitch potentiometer P1 and soldered in a generic Jellybean transistor in place. Then I added a 3.5mm jack for a CV input and simply soldered it with a
voltage divider and rather large base resistor to the transistors base until I got a somewhat usable range of pitch. Obiously the scale was completely out of tune and far from linear, but It was enough to demonstrate that the thing can be used to produce melodies.

https://github.com/TU-DO-Makerspace/Dampflog/assets/12089409/d06b69a9-8a2e-4bfc-8f98-e92429bd2175

#### Time to get serious

Implementing pitch control became a weeks-long journey. By the end I had suffered from serious circuit design brain-rot. Prior to working on this project, my experience with analog operation of transistors was somewhat limited. This was further complicated by attempting to implement 1V/Oct pitch control on a circuit that was never originally designed for such a purpose. I also wanted to avoid altering the original circuit as much as possible.

After some initial, albeit clueless experimentation with transistors, it became very clear that I couldn't sidestep a deeper understanding of these components if I wanted to achieve precise 1V/Oct control. Fast forward a few weeks, and I had consumed over 40 hours of electronic circuits lectures delivered by Prof. Behzad Razavi from the University of California in Los Angeles, which are freely available online. I can't emphasize enough how invaluable these lectures were, providing a significantly more comprehensive and insightful overview of transistors compared to my university's electronic circuit course. After absorbing a substantial amount of knowledge from these lectures, I felt ready to take a more educated approach to solve the pitch control conundrum.

First, I examined how some Voltage-Controlled Oscillators (VCOs) implement 1V/Oct pitch control. Typically, this involves exponentializing a linear signal using a transistor. This exponentialization is necessary because human perception of pitch is inherently exponential. In the equal-tempered scale, for instance, the frequency of notes increases exponentially by the twelfth root of 2. Of course, the implementation goes beyond simply connecting a transistor's base to the 1V/Oct input; it typically includes circuitry for gain calibration, scaling, and base note adjustment. However, these details need not haunt us, as this approach cannot be directly applied to our oscillator anyaways.

Here's the crux of the issue: our oscillator exhibits inverse-multiplicative growth, something akin to the form a * 1/x + b. 

![Frequency vs Resistance Response](docs/P1_FreqVSRes.png)

This response is neither linear nor exponential. If it were linear, we could simply use a transistor to exponentialize it and achieve 1V/Oct pitch control. If it were already exponential, we could use a transistor with heavily supressed gain, thus operating it nearly lineary (akin to a voltage-controlled resistor). Unfortunately, the oscillator's response falls into an awkward zone where it somewhat behaves like an exponential function but not quite. Yes, Low frequencies experience a slow rate of change, and high frequencies experience a rapid rate of change, but it's still not quite exponential. To test the extent of this inaccuracy, I decided to construct a test circuit with a transistor that roughly operated as a voltage-controlled resistor. To achieve this, I selected an extraordinarily large base resistor (around 5M in this case) to suppress the transistor's gain to the point where its beta value and base resistor dominated the gain.

The next step involved sweeping the transistor's base voltage using a function generator and measuring the oscillator's frequency. The outcome was predictably disappointing. As anticipated, the response exhibited inverse-multiplicative behavior, with the oscillator stabilizing at high frequencies. I unfortunately only measured the frequency response within the operating range of the
transistor, so to better illustrate the inverse-multiplicative behavior the graph below shows the frequency to base voltage response on a equivalent LTSpice simulated circuit:

<p align="center">
<img src="docs/SimBaseVsFreq.png">
</p>

It should be noted that the real oscillator does not reach frequencies below 116Hz, other than that the response is similar enough to demonstrate my point.

Notice the grey lines in the graph. These represent note intercepts. Taking a quick glance at the note intercepts, it becomes apparent that the response only approximates exponential pitch within an exceedingly narrow range. Ideally we'd want them to be equally spaced on the x axis to implement 1V/Oct. If we plot the distances between each note intercept, this discrepancy becomes even more pronounced. Here's actual data from the real oscillator:

<p align="center">
<img src="docs/DeltaNotes.png">
</p>

As we can see pitch only behaves linearly proportional around 3.5V with a steps size of about 60mV/Note. For the setup in question, 3.5V corresponded to approximately 300Hz, which falls within the 4th octave. As we leave 3.5V this proportion begins to drift away from the close to constant 60mV, which will cause the pitch to become out of tune.

<p align="center">
<img src="docs/DeltaNotesOP.png">
</p>

I actually went so far as to construct a 1V/Oct scaling circuit to connect my Keystep keyboard. While I achieved reasonably linear behavior in the fourth octave (as corresponding to the "sweet spot" where the inverse-multiplicative function is most similar to the exponential pitch function), venturing beyond the octave unsuprisingly resulted in severely out-of-tune frequencies. This deviation escalated significantly the further we moved away from this "sweet spot."

#### Screw CV, we're going full MIDI

At this point, it dawned on me that trying to tackle the inverse-multiplicative quirk with analog wizardry just wasn't worth the headache. I should probably mention that I'm currently pursuing a degree in computer engineering. Now, you know how it is – us computer engineers often enjoy poking fun at electrical engineers by solving problems with lines of code instead of soldering irons. Jokes aside, it really seemed like the easiest and most practical solution here was to go digital, and more specifically, to embrace the wonders of microcontrollers and DACs. And if we're making the switch to digital, why not go all the way and swap out CV with MIDI?

The idea is pretty straightforward: the MCU receives MIDI signals via a MIDI port, then converts them into DAC values using a handy lookup table. These DAC values, in turn, dictate the behavior of a transistor nestled within the oscillator's feedback path. Now, we no longer need to fuss about the intricacies of whether the oscillator operates linearly or exponentially. All we have to do is tell the MCU which note corresponds to which DAC value, and presto – we've got the right frequency.

![MIDI Ports](docs/Midi.JPG)

With a DAC, it's still important to maintain control over the transistor's gain suppression while ensuring that the gain remains substantial enough to cover the oscillator's full frequency range with the MCU's and DAC's supply voltage. For the DAC, I opted for an MCP4921, which has 12 bits of resolution and the convenience of an external reference voltage. This choice proved more than adequate for accurately mapping MIDI data to the oscillator's frequency range, and that despite loosing a portion of the DAC range due to the absence of biasing its output to the operating range of the transistor.

#### A PCB to rule them all

In order to create a digital interface for controlling the Dampflog, it became evident that a PCB would be practical for the task. Consequently, I proceeded to designing a PCB that incorporates various key elements, including MIDI circuitry, an STM8S development board as MCU, a DAC, and a couple of additional features like a GATE output and portamento functionality. The GATE output allows for MIDI-based GATE control. Additionally, I integrated switches to transition between manual oscillator operation and digital control. For the GATE function, I simply applied an OR logic operation to the MCU's GPIO output and the previously implemented analog GATE inputs. This spared me from having to add another switch, which would convolute the device even more.

![Interface Board Schematic](docs/InterfaceBoardSchematic.png)

![Interface Board PCB](docs/InterfaceBoardPCB.png)

It's worth noting that I designed the PCB to fit within a single layer, allowing for in-house etching. The red traces represent jumper wires. In retrospect I was rather naive about the clearances, which lead to some challenges during the etching process (some traces were close they ended up shorting). Despite these hiccups, the PCB eventually performed its intended function.

![Interface Board](docs/InterfaceBoardBuilt.jpg)

Now, I won't delve into further details of the interface board in here, as it deserves a dedicated README of its own. You can find comprehensive coverage of the interface board, including insights into the MCU's firmware, in the README file within the InterfaceBoard directory.

## The Result

Here's the final block diagram of the circuit, including the interface board:

![Final Block Diagram](docs/DampflogBlock.png)

So, what I've got here is a steam locomotive whistle synth that's grooving to the MIDI rhythms. It's kinda hilarious to think that someone originally snagged this thing for their model train setup, and now, more than two decades later, it's belting out some seriously gritty techno tunes.

Let's be real, this thing has no business being so absurdly over-engineered, especially when you consider its somewhat limited frequency range and the fact that it probably won't exactly blow your mind with its sound. But that doesn't matter because this project was an absolute blast! I learned more about transistors in a few months than I did in my entire four years of studying! Plus, I dove headfirst into the world of pitch scaling, data analysis, signal wizardry, and the art of wrangling DACs. Now that's something!

## Future plans

Right now, I'm just happy to call this project a wrap. Don't get me wrong, it's been lot's of fun, but honestly, at this point I just want to crank it up and start making some music. That said, I've got some ideas brewing in the back of my mind. I'm thinking about cooking up a standalone synth or maybe even diving into the world of eurorack modules with this thing. I'd essentially take a stripped-down version of the train whistle PCB and give it multiple voices by using multiple oscillators instead of just one. It should be a pretty straightforward endeavor since most of the ICs I'd need for this task come in dual and/or quad packages.
