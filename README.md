# Random-looking number generator

## Instructions

Usage (Python 3):

```
python generate_numbers.py
```

Typical output:

```
Best sequence with a length of 25 and a number pool with size 5:
[3 5 1 3 4 1 2 3 1 3 2 3 2 5 4 3 1 4 2 3 4 5 1 3 4]
Flaws of this sequence:
1 directly mirrored patterns (e.g. 1 2 3 2 1)
3 steadly increasing or decreasing series (e.g. 1 2 3)
29 repeating sub-patterns (e.g. 1 2 3 1 2)
Total score: 4.39 (zero would be ideal)
```

External dependencies:

* tqdm (optional - for the progress bar)
* numpy (obligatory - for all the math)


## Background

When drawing from a small pool of choices, random number generators can randomly generate meaningful shapes.

For example, I'll produce a patch of random colors:

```
[Python]
import numpy as np
from PIL import Image
a = np.random.rand(3,30,3)
i = Image.fromarray(a, mode='RGB').save('r.png')

[Terminal]
magick convert r.png -colors 5 -scale 1000% random_colors_30x3.png
```

![wide patch of randomly colored squares](random_colors_30x3.png)

This supposedly random patch clearly shows some non-random features. I can see

* three Tetris blocks: ![tetris](example_tetris.png)
* two checkerboard patterns: ![checker](example_checker.png)
* five L-shapes: ![l-shapes](example_l-shapes.png)
* five vertical lines that suspiciously all start in the top row: ![lines](example_vertical.png)

After removing just the most obvious patterns, we're left with only 41 pixels that a regular human would described as "random". That's less than half of the original pattern.

This problem is typical for all types of random number generation that draws from a small pool of possibilities. For example, here's ten random numbers between 1 and 10:

```
np.random.randint(1,10,10)
[6,9,9,7,8,4,8,8,8,3]
```

The core of this problem isn't that random generators are bad, it's that humans are too good at finding patterns in random noise. That's why I built something that avoids these patterns.

## Principle

In simple terms, the code does this:

* generate a sequence of random numbers
* try to find all human-readable pattern
* try to find out how visible these patterns are to a human
* calculate a penalty value for these patterns
* repeat from the top a few hundred times
* print the sequence with the lowest penalty value

In more detail, there are three different pattern recognition algorithms.

#### Pattern #1: the mirrored sequence
8 **2 6 2** 4 3 6 9 5 2

Note that this algorithm currently only detects patterns with a length of three. Detection of a mirrored pattern with arbitrary length requires a different approach.

#### Pattern #2: the linear sequence (rising or falling)
rising: 2 5 1 6 2 **4 5 6 7** 3

falling: 8 2 **4 3 2 1** 4 3 7 4

The minimum length that counts as a linear sequence is 3.

#### Pattern #3: the repetition (immediate or distant)
immediate: 9 4 8 **7 7** 1 9 **2 2 2**

distant: 1 **2 8 3** 7 4 **2 8 3** 5

All detection algorithms calculate their own penalty terms, and the sum of these terms is ultimately used to rank the random sequences.

## Penalty calculation

The calculation uses three components:

* H - a fixed base value, specific for each type of pattern. Typical value: 1.5
* s - the length of the detected pattern. Typical value: 2
* Ω - a mitigation term. Usually Ω = 1, except for the "distant" case in pattern #3. In that case: Ω = [distance between the closest two duplicates] ^ 1.5.

The formula (identical for all three algorithms):

penalty = ((H ^ s) - 1) / Ω

## Possible improvements

First, the amount of sequences that are generated before the winner is selected is mostly guesswork. It's tested for sequence lengths between 10 and 50 and item numbers between 5 and 10 and may be completely inadequate outside these limits. Currently the amount of attempts grows linearly with sequence length.

I can imagine there to be a good heuristic that estimates the necessary number of attempts from sequence length and size of the item pool. However, since I've only used this project for small sequences so far, the typical computation time of five seconds hasn't warranted any additional effort.

A routine that stops the calculations once the penalty term hits zero ("early stopping") may be a low-effort addition though.

Second, I haven't profiled any of the core algorithms. When generating much longer sequences, optimizations may become neccessary and may even be trivial for a Python expert. That said, I've at least attempted to find the fastest implementation for each of the three tasks.

Third, the algorithm for detecting pattern #1 is more limited than the other two. This was a time/effort constraint rather than an ideal solution. Overhauling this algorithm would round off this project, but I doubt that I'll ever accomplish that.

Finally, a new algorithm that makes sure that the histogram is balanced could be nice too. 