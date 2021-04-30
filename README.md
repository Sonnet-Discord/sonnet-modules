# sonnet-modules
A repo of sonnet command modules and dlib modules that extend sonnet to more obscure tasks  
This repo is open to all to submit their own modules or patch others
# Guidelines
- Modules should be submitted as /mod/<username>/<modulename>/\*
- Modules will include a README.md explaining:
  - What they do 
	- Sonnet configs named
	- Custom DB tables named
	- Minimum sonnet version they require
## Example:
```bash
> ls GITROOT/mod/ultrabear/marketrep/
README.md cmd_marketrep.py
> cat GITROOT/mod/ultrabear/marketrep/README.md
# Market Rep
This is a simple command module that implements tracking market rep of members
# Configs used
- `mr-roles`
# DB tables used
- `marketrep`
# Min sonnet version
- V1.2.3
```
