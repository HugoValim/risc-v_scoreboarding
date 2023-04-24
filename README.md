# This is a simulator for out of order execution of RISC-V assembly using the scoreboard algorithm

# You can run the code in multiple ways, in all the listed methods below you can input a flag to tell the program if it should print all the stages or just the final result

## pip install the project and use the command "scoreboarding_sim". The inputs are the configuration file with instructions and the Functional Units configuration. All the inputed information can be in a single file or spreaded in several files, just pay attention to input instructions in the correct order

```
git clone https://github.com/HugoValim/risc-v_scoreboarding
pip install -e risc-v_scoreboarding
```

### In shell:

```
scoreboarding_sim test_1.txt test_2.txt -p
```

## Import the module and use it:

### Run some tests over the data contained in this project in folder risc-v_scoreboarding/sbsim/tests/data/
```
from sbsim import main
main()
```
### Import and run you own files with it:
```
import sbsim
run = sbsim.ScoreboardingSIM([<path to file 1>, <path to file 2>], False)
run.execute()
```

## Or you can just run it from the risc-v_scoreboarding/sbsim/scoreboarding.py file directly
### You must use the class contained in it to run your files, there is a main function in it with some examples in how to run it
