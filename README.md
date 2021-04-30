# sonnet-modules
A repo of sonnet command modules and dlib modules that extend sonnet to more obscure tasks  
This repo is open to all to submit their own modules or patch others
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
	"events":[],
}
```
