# MEC-Simulator 2 (BigMEC)

This is a simple simulator for distributed, learning service placement strategies for mobile edge computing (MEC).

***

This software was used to evaluate the data for the publication

[BigMEC: Scalable Service Migration for Mobile Edge Computing](https://brandherm.info/wp-content/uploads/2022/11/brandherm2022BigMEC.pdf)

Florian Brandherm, Julien Gedeon, Osama Abboud, Max Mühlhäuser

Symposium on Edge Computing, 12/2022

### Setup

* Check out the `Dockerfile`/`requirements.txt` for installing dependencies or build the docker image.
* Start the program with `python3 main.py`

| Command Line Parameter           | Explanation                     |
|---------------------------------:|:--------------------------------|
|`-h`, `--help`                    | Documentation of cli parameters |
|`-x`, `--headless`                | Disable GUI. Otherwise a visualization will be displayed. |
|`-c FILE`, `--configuration FILE` | Configuration file. If none is specified, interactive mode will ask to choose one configuration from the folder `defaultExperimentConfigurations`. |
|`-o DIR`, `--output DIR`          | Specify an output directory for the experiment logs. If not specified, the default directory is `./output`. |


### Experiments

The experiment scripts used in the paper evaluation are contained in the folder `experiments/SEC/`

***