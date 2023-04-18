# This is a simulator for out of order execution of RISC-V assembly

## The easiest way to use this project is clonning it and

### pip installing the project:
```
git clone https://github.com/HugoValim/risc-v_scoreboarding
pip install -e risc-v_scoreboarding
```
### Run some tests:
```
from sbsim import main
main()
```

## You can run the code in multiple ways:

### Via shell, using the command "scoreboarding_sim":
```
scoreboarding_sim test_1.txt test_2.txt -p
```

### By importing and running it:
```
import sbsim
run = sbsim.ScoreboardingSIM([<path to file 1>, <path to file 2>], False)
run.execute()
```

