# LogBuddy

- [LogBuddy](#logbuddy)
  - [Currently supported log files](#currently-supported-log-files)
  - [How it works](#how-it-works)
  - [Example](#example)
  - [Running](#running)

This tool is "actively" being developed! Make sure to check for updates from time to time, they might add a cool feature!

LogBuddy is a helper tool for reading log files. It has features to:

- combine multiple log files
- sort them however you want
- filter out logs by who performed the action, where it happened
- filter out logs that a person couldn't have heard or seen
- work with multiple filters (filter the filtered output)
- write the resulting set to a file

## Currently supported log files

- game.txt
- attack.txt
- pda.txt
- silicon.txt
- virus.txt
- paper.txt
- mecha.txt
- telecomms.txt
- uplink.txt
- shuttle.txt

## How it works

When starting the application with parameters, a variable called `main_file` is created, which
contains all lines from all log files provided, sorted by time. Any function called accesses and
modifies the `work_set` variable of your `main_file`, so you may chain multiple functions.
To reset the work set, call `main_file.reset_work_set()`.

## Example

In this example it's assumed you ran the application with no command line arguments (double clicking
on the executable).

At any point feel free to type `help` for general help, or `help(thing)` for help with that specific
thing (for example `help(LogFile)`).

First, we download (there is an easier alternative, keep reading) our logs to a folder. Let's name the
folder `logs`. The folder will be in the same parent folder as the executable (or script), so we don't
have as much to type. For this example feel free to download as many (or just one!) supported log files
as you'd like. The list of supported files is just above.

As an alternative you can use
`my_log = LogFile.from_logs_line("https://tgstation13.org/parsed-logs/terry/data/logs/2022/03/18/round-180150/")`
(the link should be replaced with your own). This will automatically download all available log files.

To load the whole folder (and save the result to a variable), we use `my_log = LogFile.from_folder("logs")`.
If your logs folder is somewhere else, just type out the whole absolute or relative paths (for example, `../logs/`).
To load just one file, use `my_log = LogFile.from_file("game.txt")` (assuming you want to load game.txt).
You can later add another file by doing `another_log = LogFile.from_file("attack.txt")`. To combine them use
`my_log.collate(another_log)`. This will modify `my_log` to incorporate the other log object's logs.

The variable name completely depends on you, you can pick any name you want (usually all lowercase with
underscores instead of spaces). Just don't forget to replace `my_log` with your name.

When loading logs you may see some errors. It's usually fine to ignore them, unless there's many of them.
Sometimes there are strange and uncommon ways to log things, and it's hard to account for all of them.

If you have a public logs website (see: [this link](https://tgstation13.org/parsed-logs/)), you can use
`my_log = LogFile.from_logs_link("link_to_root_of_files")`. You know you have the right link when you see
many different log files displayed. An example of the full link is can be seen
[here](https://tgstation13.org/parsed-logs/terry/data/logs/2022/03/01/round-179256/).

Before getting started you may want to see some stats. To see the amount of log lines loaded, run
`len(my_log.logs)` (or `main_file` if you're using the default variable). To see the list of all
players that connected during that round, you can run `my_log.who`, or `len(my_log.who)` for the
number of players that have connected.

Now that we have a log file ready, let's filter it. We want to find out if someone has been running
around and destroying windows. Firstly, let's filter out only their ckey like so
`my_log.filter_ckeys("WindowSmasher32")` (sidenote: notice the s in ckeys. This means you can filter
for multiple: `my_log.filter_ckeys("WindowSmasher32", "FireaxeLover2", "CoolCkey53")`. We can view
the result by calling `my_log.print_working()`. We're not done yet, we can go further than this. Let's
filter out everything (in the result), that doesn't contain a window. To do this, we can call
`my_log.filter_strings("window")`. This works a lot like CTRL + F. To write our result to a file, we
can use `my_log.write_working_to_file("logs.txt")`, which will write our working set to `logs.txt`.

But why not just use a text editor for this? Here's why. Let's say someone's been lying, and you want to
know if they heard someone say something. You could either go searching by hand, or call
`my_log.filter_heard("Liar54")`. It doesn't work perfectly, but it's better than not having it, right?
To reduce our work set further, we can call the same functions as before.

This is only the surface of what you can do. Python knowledge comes in handy here. Since this is a
Python interpreter running in the background, you can do anything you would in Python. Run a file,
write a custom sort function, the world's your oyster!

## Running

Download [this executable](https://github.com/RigglePrime/LogBuddy/releases/latest) OR

Quick tip: the colours on your terminal might not look that great, especially if you're using Windows.
I strongly suggest running it with Windows Terminal, as it has MUCH nicer colours. Simply download it
(I'm sure you can figure out how to do that), open the Terminal (try right clicking near the executable,
you may get an option to "open in Windows Terminal", if not use "`cd <directory>`, or `cd ..` to go back),
and run the executable from there (type the name out).

Using Python:

- `pip install -r requirements.txt`
- `python LogBuddy.py`

Optionally:

- `python LogBuddy.py logs`, where `./logs/` is a folder that contains logs (all will
be parsed)

I recommend creating a virtual environment, but it's not necessary. If you don't
know how to do it, you probably don't need to worry about it. If you run into
strange issues, start worrying about it.

Optionally, you can provide a log file, or folder with multiple log files.
The script will automatically load those in. You also manually do it later.

Made in Python 3.9
