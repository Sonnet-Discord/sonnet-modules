# sonnet-modules
A repo of sonnet command modules and dlib modules that extend sonnet to more obscure tasks  
This repo is open to all to submit their own modules or patch others
# Guarantees
Modules published under sonnet-modules do not guarantee backwards compatibility or stability, this repository is simply a place for people to post their creations
# Guidelines
- Modules will be submitted as /mod/\<username\>/\<modulename\>/\*
- Modules will include a README.md explaining:
  - What they do
  - Minimum sonnet version they require
- Modules will include bloat.json which documents:
  - Command names used (`"commands":[]`)
  - DB table names used (`"tables":[]`)
  - Sonnet config names used (`"configs":[]`)
  - Event names used (`"events":[]`)
  - Config caches used (`"caches":[]`)
  - Filenames used (`"files":[]`)
  - Version (`"version":"0.0.0"`)
- Modules may specify lib_ files used
  - This change was made to allow code deduplication between a dlib and cmd file under the same module
  - Files named cmd_\*.py will be under cmds, dlib_\*.py under dlibs, and lib_\*.py under libs
## Example:
```bash
> ls GITROOT/mod/ultrabear/marketrep/
README.md bloat.json cmd_marketrep.py
```
GITROOT/mod/ultrabear/marketrep/README.md
```md
# Market Rep
This is a simple command module that implements tracking market rep of members
# Min sonnet version
- V1.2.3
```
GITROOT/mod/ultrabear/marketrep/bloat.json
```json
{
	"commands":["mr-add", "mr-remove", "mr-addrole"],
	"tables":["marketrep"],
	"configs":["mr-roles"],
	"caches":[],
	"files":["cmd_marketrep.py"],
}
```
Note: as no `events` are used by this module it omits writing the json key to an empty list, this holds true for all keys
