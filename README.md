# Dampflog

![Showcase]()

A synthesizer built from an [old Conrad Train whistle PCB](docs/DLP_Manual.pdf)! This project was created during the [TU-DO Makerspace's Makerthon #1](https://www.instagram.com/p/CwGRmoHKHiY/?igshid=MzRlODBiNWFlZA==).

## "Dampflockpfeife" - The Steam Locomotive Whistle

### Product Description

The "Dampflockpfeife" (Product ID. 19 77 77) is a Printed Circuit Board that was published by conrad in 1997 as a DIY soldering set for model train enthusiasts.
It attempts to mimic the sound of a steam locomotive whistle upon "triggering". The intended use is to likely be installed in a model train track and be triggered by a passing train. The PCB contains two potentiometers: One for the pitch and one for the whistle duration. To trigger the sound, two contacts on the PCB need to be shorted (ex. via some button or sensor).

Here's a showcase of how the Whistle sounds:

INSERT VIDEO HERE

### The Circuit

Given the time of publication, it shouldn't come as a suprise that the circuit contains no digital components. The whistle sound is synthesized completely anagously.
Thankfully the manual of the PCB is freely available online (see [docs/DLP_Manual.pdf](docs/DLP_Manual.pdf)) and contains everything from a circuit description to a full schematic and even a PCB layout. Obviously the manual is in German, but no worries, the circuit will also be covered here!

Here's the schematic of the circuit:
![Schematic](docs/schematic.png)

The circuit can be split into four parts:

- 1. Power stage
- 2. Trigger/Gate circuit
- 3. Oscillator
- 4. Output Stage/Amplifier

Here's a block diagram of the circuit:
![Block diagram](docs/block_diagram.png)

#### 1. Power stage

![Power stage](docs/power_stage.png)

I found it a little odd, but the circuit takes a AC voltage as input. I suppose this was chosen to be compatible with "Märklin" model train tracks, which unlike their
competitors use AC voltage. Sources claim this voltage ranges from 16 to 24V. I am no expert in model trains, however I did coincidentally come in contact someone who knew a thing or two about model trains and they explained me that the whole AC voltage thing is a quirk of Märklin.

Anyways, back to the circuit. The AC voltage is rectified by a full bridge rectifier (D1-D4) and then filtered by a 100uF capacitor (C12). The smoothed voltage is then regulted down to 12V by a 7812 linear regulator (IC1). The 12V are then used to power the rest of the circuit.

For my intents and purposes, the whole power section was not needed. I simply used a 12V DC power supply and connected it directly to the 12V rail.

#### 2. Trigger/Gate circuit

One symbol in the schematic that quickly caught my attention was the NE555 timer IC. Initially I assumed that it is responsible for the tone generation, however it is actually operated in [monostable/one-shot mode](https://fulmanski.pl/tutorials/electronics/introduction/555-2/#basic_example_monostable) to generate a temporary gate signal. The gate signal is used to trigger the oscillator and amplifier. Its duration is configured by the potentiometer P2. The duration can range anywhere from 1 - 10 seconds depending on the potentiometer setting. To trigger the gate signal, the switch marked with the text "Start" must be closed which will
pull down the trigger input of the NE555. This will cause the NE555 to output a high signal for the configured duration at the output pin 3, which in return forward biases the transistor T3. Since the collector of T3 is connected to the base of T2, T2 will will now be reverse biased. By default, T2 is forward biased by the pull-up resistor R4, which pulls the feedback path of the Oscillotr to low and thus prevents it from outputting a tone. When T2 is reverse biased, the feedback path is no longer pulled down and the oscillator is free to oscillate and thus synthesize a tone.

#### 3. Oscillator

The oscillator is the heart of the circuit and hence perhaps also the most complex part of the circuit. It somewhat resembles an OP-AMP (In this case an LM741) relaxation oscillator with a couple of quirks. Firstly, the positive feedback path is AC coupled via C1, and C2. Secondly, and this is what makes the circuit so interesting, the feedback path contains an NPN transistor T1 which is configured in a very atypical and quirky way, that is in diode configuration with it's emitter attached to the more positive rail, to feed noise into the feedback path. If that wasn't odd enough, the op-amp output is also coupled to the "Offset Null" pin of the op-amp via capacitor C7. The purpose of the transistor T1, as well as the Offset Null feedback is to induce noise into the feedback path by causing slight shifts in the oscillators frequency. This is what gives the circuit its characteristic "steam locomotive" sound. As mentioned, the rest of the circuit resembles am OP-AMP relaxation oscillator. The frequency of the oscillator can be adjusted via the potentiometer P1 which pulls down the propagated through the positive feedback path. On the inverting input of the OP-AMP, a triangle wave is formed due to the RC circuit formed by R8 and C6. The smaller the resistance of P1, the lower the voltage that is propagated through the positive feedback path. This in turn means the triangle wave at the non-inverting input can "catch up" the voltage at the inverting input faster, which in turn increases the frequency of the oscillator. At some resistance, P1, the porpagated voltage is so low enouhg that the oscillation stabilizes. During this
operation, only the sound generated by the noise feedback path is audible, which can only be described as eery and perhaps even a little creepy. A recording of this sound can be found [here](https://soundcloud.com/user-631734174/bc548-diode-configuration-noise). Another interesting side effect of stabilizing the oscillator is that it experiences hysteriesys due to it's schmitt-trigger like positive feedback. As a result, the potentiometer P1 must be turned a futher back to restart the oscillation.
In total, this oscillator offers a frequency range of approximately 116Hz (inf resistance) to 700Hz (point of stabilization). That's about 2.5 octaves of range (A#2 - F5).

Below are a couple of screenshots of LTSpice simulations to
illustrate the behaviour of the oscillator.

LT SPICE STUFF HERE

One thing that is very important to know is that the frequency vs P1 behaivour experiences a rather inverse multiplicative behaviour. At low resistances (high frequencies), the frequency experiences very fast changes with small changes in P1. At high resistances (low frequencies), the frequency experiences very slow changes with small changes in P1. For well-tampered pitch, this behaivour should be exponential and as we'll see this was a major issue later when attempting to implement 1V/Octave pitch control.

Another interesting property of the LM741 is that higher frequencies experience a low-pass behaivour. In lower frequencies we get a more square-ish output, in higher
frequencies we get a more triangle-ish output. This is likely due to the slew rate of the LM741 and actually adds some nice character to the sound.

#### 4. Output Stage/Amplifier

Truth be told, I am not an expert regarding transistor amplifiers and since the output stage is not really relevant for my project I have not even attempted to
inspect it in more detail. I'm not entirely sure, but I assume T4 and T5 are there to amplify the voltage of the signal and the complementary push pull amplifier formed by T7 and T6 buffer the current? Please correct me if I'm wrong.

## Hacking the PCB

After analyzing the circuit it was time to turn the PCB into a synthesizer. Before grabbing my soldering iron I had to think about what features I wanted to add to the PCB to turn it into a synthesizer. Here was my initial list of requirements:

- 12V DC Power Input
- 3.5mm Jack audio output with volume control
- A HOLD switch to permanently enable the gate signal
- A 0-5V Gate input to trigger the gate signal
- A 1V/Octave CV input to control the pitch

In addition to these features, I also wanted to ensure that the device could still be operated in it's original inteded way. For that I ensured to add a push button to trigger the gate signal, as well as a potentiometer to control the duration of the gate signal and a potentiometer to manually control the pitch.

To house the PCB I used an old metal box that used to contain a [data transfer switch (KVM Switch)](https://www.amazon.com/Kentek-Parallel-Peripherals-Devices-Printer/dp/B07KWRWLRN) which we had lying around in the makerspace. Under typical circumstances I would have probably just 3D printed an enclosure, however, as mentioned earlier, this project was created during a Makerthon, so I simply didn't have the time to design and print an enclosure. I also gave the enclosure a cute little
spray paint job just for the fun of it.

### Power Input

Adding a 12V DC power input was rather trivial. I simply soldered a 2.1mm DC barrel jack to the 12V rail of the PCB with a switch in between to turn the device on and off. I also added a small red power LED next to the Jack to indicate that the device is powered on. I tried to solder the power wires as close to the power stage as possible to maximize use of the power capacitors on the PCB. The jack is mounted on the front side of the enclosure and the switch is mounted on the back side of the enclosure. In hindsight, I should have probably swapped the positions of the jack and the switch, since it would have made the device more ergonomic to use. However I only considered adding the switch after I had mounted the jack in place.

PICTURE OF JACK HERE

### Audio Output

Adding audio output was quite straight forward. I simply soldered a 3.5mm audio jack to the output of the amplifier. I also added a potentiometer as voltage divider to control the volume of the output signal. The jack along with the potentiometer are mounted on the front side of the enclosure.

PICTURE OF AUDIO JACK HERE

### Original Controls

As mentioned earlier, I wanted to ensure that the device could still be operated in it's original intended way. For that I ensured to add a large green arcade push button to trigger the gate signal, as well as a potentiometer to control the duration of the gate signal and a potentiometer to manually control the pitch. The push button is mounted on the top side of the enclosure and simply connected to the trigger input of the Monostable 555 as original Intended. The potentiometers to control pitch and duration are also mounted on the top side of the enclosure. For the pitch I've actually switched the 50k pot with a 200k pot to get a better range of pitch. 50K does not quite reach the lower frequency limits of the oscillator.

PICTURE OF ORIGINAL CONTROLS HERE

### HOLD Switch

Adding a HOLD switch was perhaps the first not so trivial addition to the circuit. After some thinking I concluded that a switch in parallel to transistor T3 would do the trick best. When the switch is closed, it essentially has the same effect as if T3 was forward biased, which in turn means that T2 will reverse biased and the oscillator will always be enabled.
The hold switch is mounted to the top right of the trigger button.

SCHEMATIC MOD

PICTURE OF HOLD SWITCH HERE

### Gate Input

To add a GATE signal I simply took inspiration from the HOLD switch and added a 3.5mm jack connected to a NMOS transistor in parallel to T3. To ensure that the mosfet is always turned off when the jack is not connected, I added a 220k resistor between the gate and source of the mosfet. I also added a 10k resistor between the jack tip and the gate of the mosfet to increase the RC constant and thus ensure that accidental voltage spikes cannot fry the MOSFET (ex. when the jack cable is being plugged in).

SCHEMATIC MOD

PICTURE OF GATE JACK HERE

Without spoiling too much, the GATE input has been modified a little later on in the project.

To test out GATE support, I connected my trusty Arturia Keystep to the GATE input and realized that the oscillator isn't really ideal for GATE input, at least not in a traditional sense. See, the oscillator unfortunately has a slight attack duration and short decay time which means it takes a decent amount of time for it to reach its inteded pitch but quickly shuts of once the GATE signal is dropped. As a consequence, fast GATE signals don't give the oscillator enough time to reach its pitch and the tone just ends up getting "chopped". Thsi is largerly due to the fact that the oscillator relies on RC circuits which by intention take time to charge up. I thus found GATE to only be useful in two cases:

1. When the BPM/tempo is slow enough to allow the oscillator to reach its intended pitch
2. To crease a percussion-like choppy sound

I actually found the second case to be a seriously cool unintended feature, especially when the oscillator is capped out so that only the noise in the feedback path is getting gated. It gives the device a really rough old-school industrial sound. A sample of how this can sound with a bit of distortion, reverb and flanging can be found [here](https://soundcloud.com/user-631734174/dampflog-gate-noise-test).

### Pitch Control

Let me start of by warning you that Pitch control was by far the most difficult part of this project. Hence, this chapter developed into quite the rabbit hole.

#### Initial Approach

To at least deliver a proof of concept for the end of the Makerthon I had to at least implement some form of half-arsed pitch control. For the sake of demonstration I
disattached the Pitch potentiometer P1 and soldered in a generic Jellybean transistor in place. Then I added a 3.5mm jack for a CV input and simply soldered it with a
voltage divider and lather large base resistor to the transistors base until I got a somewhat usable range of pitch. Obiously the pitch range was completely out of tune
and far from linear, but It was enough to demonstrate that the thing can be used to produce melodies.

INITIAL DEMONSTRATION

#### Time to get serious

Enter weeks of Pitch controll brain rot. You see, prior to starting this project, I wasn't really that experienced with analog operation of transistors. It also certainly didn't help that I was completely on my own when it came to implementing 1V/Oct pitch control on a circuit that was never intedded to be operated in such way.
After a bit of clueless experimentation with transistors I quickly learned that I can't skip my way past understanding transistors If I want to get this thing to speak bloody 1V/Oct. Fast forward a couple of weeks and I had watched over 40 hours of electronic circuits lectures by Prof. Behzad Razavi from University of California in Los Angeles. I cannot stress how great their lectures are, as they've provied a signficantly better and more in-depth overview of transistors than my Universities Electronic Circuit course has. After watching 30 some lectures I felt like I had gathered enough knowledge to take an educated approach at solving the pitch control problem.

First, I took a look at how some VCO's implement 1V/Oct pitch. Typically the approach is to exponentialize the linear signal using a transistor. The signal needs to be exponentialized because humans perceive pitch exponentially. In the case of the equal-tampered scale, the frequency for notes grows exponentially by the twelth root of 2. Obviously there's a little more to the implementation than just slapping a transistor after the base. There's typically also going to be circuitry to calibrate the gain, scale and the base note but I won't haunt you with all the details as this approach unfortunately cannot be applied directly applied to the oscillator.

See, the problem with our oscialltor is that it experiences inverse-multiplicative growth, that is, something along the form of `a * 1/x + b`. We can see this in the following graph which displays the frequency of the oscillator in relation to the resistance of the pitch potentiometer P1:

GRAPH HERE

This sucks, because this is neither linear nor exponential. If the response was linear, we could simply exponentiaze it with a transistor and get it to speak 1V/Oct.
If it were already exponential, we could also use a transistor and supress the gain to the point where it behaves nearly linearly (ie. like a voltage controlled resistor). An inverse multiplicative response leaves us in an akward zone where it sorta behaves like an exponential function, in that low frequencies experience a slow rate of change and high frequencies experience a fast rate of change, but it's not quite exponential. To see how inaccurate the response is, I decided to build a little test circuit with a transistor approximately operating as a voltage controlled resistor. To achieved this, I chose a very large base resistor (about 5M in this case) which supresses the gain of the transistor to the point where its beta value and base resistor dominate the gain. This conclusion came after perfoming a small signal analysis of the transistor and oscillator as shown below:

SMALL SIGNAL ANALYSIS HERE

Then it was time to sweep the transistor's base voltage using a function generator and measure the frequency of the oscillator. The result was unexpectedly disappointing. As expcted, the response is inversely multiplicative, except for high frequencies where the oscillator dies.

INSERT GRAPH

If we analyze the output for note intercepts we can see that the response only approximates exponential pitch in a very narrow region. If we plot the distances between each note intercept, this becomes even more so apparent:

INSERT GRAPH

INSERT GRAPH

I event went as far to create a 1V/Oct scaling circuit to connect my keystep and while I got rather linear behaivour in the 4th octave, which corresponds to the "sweet spot" where the inverse multiplicative is most similar to the exponential pitch function, leaving the octave quickly resulted in a very out of tune frequency. This is because the deviation significantly increases the further we move away from the "sweet spot".

SHOWCASE

#### Screw CV, we're going full MIDI

At this point I realized that an analog solution to compensate for the inverse multiplicative behaivour would simply not be worth the effort. Now, perhaps I sould mention at this point that I'm a computer engineering undergrad. Now... I feel as a computer engineer there's almost a certain obligation to provoke electrical engineers by solving lots of issues with code instead of electronics. Sorry for triggering al EE's that are reading this. Jokes aside, it really did seems like the easiest and most plausible solution here was to work with a microcontroller, and most imporantly a DAC. And since we're already going digital here, we might as well switch to a digital alternative to control pitch, that is, MIDI.

The concept is rather simple, the MCU receives MIDI via a MIDI port, that in turn is then converted to a DAC value using a look-up table, which then in turn controls a transistor in the Oscillators feedback path. Now we don't have to care about how exponential or linear the Oscillator operates, we simply need to tell the MCU which note corresponds to which DAC value to output the correct frequency. We will also want to keep the gain supression of the transistor to gain resolution. What's important is that the gain is still large enough to reach the full frequency range of the oscillator with MCU's and DAC's supply voltage. For the DAC I chose an MCP4921 which gives me 12-bits of resolution and an external reference voltage to really make the most out of it. This turned out to be more than enough accurately map MIDI to the oscillator's frequency range, and that's despite loosing about 3/4th of the DAC range due to not biasing its output to the operating range.

#### A PCB to rule them all

To implement a digital interface to control the Dampflog, it quickly became apparent that a PCB would be needed. I thus designed a PCB that contains MIDI circuitry, an STM8S devboard, a DAC and a couple of other nice features such as a GATE output and portamento. The GATE output allows us to control GATE via MIDI. I also added some switches to toggle between manual oscillator operation and digital operation. For GATE I've simply ANDed the MCUs GPIO output with the analog GATE jack that I have implemented previously.

INSERT SCHEMATIC

INSERT PCB

If we expand the block diagram with the interface board from the beginning of the document, it now looks something like this:

INSERT BLOCK DIAGRAM

I designed the PCB to fit on a single layer board so that I could etch it myself. In hinsight I was way too naive with the clearances which ended up causing quite a few issues while etching it (traces shorting etc.). Altough a bit hacky, the PCB did end up working just fine in the end.

Now... I wont cover further details of the interface board here, as it is deserves a README on its own and is explicitly covered in the README file of the InterfaceBoard directory. There I also cover the firmware of the MCU.

## The Result

I am now left with a MIDI controllable steam locomotive whistle synth. I find it rather humerous to imagine that somebody bought this thing for their model train tracks and more than 20 years later somone is cranking out the dirties screaching techno sound with it. Truth be told, this thing has no right to be so ridiciously over-engineered, especially considering that it has a pretty narrow frequency range and really doesn't sound THAT impressive! That being said, this was a ridiciously fun project and I have learned more about transistors that in my last 4 years for studying! I also learned a lot about pitch scaling, data and signal analysis and how to use DACs.

## Future plans

For now I'm just really happy to be done with this project. Don't get me wrong, it's been lots of fun, but right now I just wanna jam out with it and make some music. That being said, I might cook up a standalone synth or a eurorack module that utilizes a stripped down version of the train whistle PCB but offers multiple voices (ie. multiple oscilators). This should be rather easy to achieve as the majority of ICs required for this task come in dual and/or quad packages.