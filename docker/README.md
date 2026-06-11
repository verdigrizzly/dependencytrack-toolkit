# Dtrack-Toolkit Batch Job Execution
Since version 2.0.0 the dtrack-toolkit supports an additional way to execute commands in a more automated manor. Each toolkit command can now be invoked via a configuration file. This service-extension provides a convenient way to run multiple batch jobs without creating a custom bashscript around the cli and helps to manage output and logging.

The service can be run via the command line and needs a path to a valid config-file
```
.venv/bin/python3 service.py config/config.toml
```

## Configuration
There are two configurations, that are mandatory for the service to work correctly.
+ Dependency-tracker core configuration
+ Batch Jobs configuration to configure tasks
+ (optional for Docker) env file

We decided to go with [TOML](https://toml.io/en/) as configuration-format for both. Since the core functionality is a seperate component an extensive documentation for this part can be found in the main documentation. After creating the configuration (as an example core_config.toml), one needs to point the application by setting the environment variable `CONFIG_PATH=core_config.toml`. To have backwards compatibality the application dynamically creates a core_config. This functionality can be found in the composer.py file.

The env file configures where to receive the job configuration from, the path of the core configuration and mailer configuration. An example can be found in this repository.

### Job Configuration
Each Job is defined by a TOML-Table entry providing the same set of fields as the cli command. Each task can be repeated multiple times with different parameters. A table-head must be surrounded by two square brackets and matches one of the provided names.

+ `[[project.count_vulnerable]]`
+ `[[project.average_finding_age]]`
+ `[[project.delete_expired]]`
+ `[[notification.assign_project]]`
+ `[[notification.update_projects]]`
+ `[[notification.remove_projects]]`

In addition to the command specific parameter, there is a set of batch job specific options available.

+ `title`: Used to label a job with a more descriptive name to .
+ `distinguish`: it from others.
+ `debug`: enable debug for logs and output file.
+ `output_file`: filepath for job result.
+ `log_file`:  filepath for logging file.
+ `priority`: job execution order.

### Job order
Jobs will be executed in a none deterministic manner, one after the other. If you need to create a custom order, specify that with the parameter `priority`. The highest one will be executed firsts. Jobs without a custom `priority` are set to `priority` 0 by default.

## Sample config 
```toml
[[toolkit.project.count_vulnerable]]
    debug=false
    min_crit="MEDIUM"
    from_tag="foo"
    log_file="log/count_vulnerable-INFO.log"
    output_file="output/count_vulnerable.json"
    priority=1

[[toolkit.project.average_finding_age]]
    title="Job avg age 2"
    debug=false
    min_crit="HIGH"
    from_tag="foo OR bar"
    exclude_classifier=[]
    output_file="output/average_finding_age.json"
    log_file="log/average_finding_age-INFO.log"

[[toolkit.project.average_finding_age]]
    title="Job ONE Execute FIRST!"
    debug=false
    min_crit="HIGH"
    from_tag="foo"
    exclude_classifier=[]
    output_file="output/average_finding_age.json"
    log_file="log/average_finding_age.log"
    priority=1000

[[toolkit.notification.assign_projects]]
    debug=false
    rule-name="team-test-mail"
    from-tag=["foo", "baz"]
    log-file="log/notification-INFO.log"
```

### Development
> **Warning**
> As of version 4, dependencytrack-toolkit makes use of coroutines using asyncio. Important to keep in mind with this library is that the initial `asyncio.run()` should only be called once inside the whole program. This has consequences for dtaas (dtracktoolkit-as-a-service), as a configuration can have many tasks. When dtaas runs many tasks, it should NOT call them in this manner `asyncio.run(count_vulnerable)`, but rather via `output = await task`. This means if a new feature is added to dtaas use the existing approach with await. This will guarantee that no problems occur with multiple event loops and that the tasks run sequentially.