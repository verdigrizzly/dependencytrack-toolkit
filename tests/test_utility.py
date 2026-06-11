from src.dtracktoolkit.utility import convert_args_to_dict, convert_cli_to_config
from dtracktoolkit.__main__ import fetch_args
import sys

def test_convert_args_to_dict():
    sys.argv[1:] = ["project", "analyze_vulnerabilities", "-c", "low", "-t", "FOO AND FIRSTTAG", "--output", "./tmp"]
    args, _ = fetch_args()
    expected = {"command": "project", "subcommand": "analyze_vulnerabilities", "debug": False, "dryrun": False, "to_config": False, "output": "./tmp", "min_crit": "low", "from_tag": "FOO AND FIRSTTAG", "exclude_classifier": None, 'from_name': None, 'parent': None, "shallow":False}
    assert convert_args_to_dict(args) == expected
    
    sys.argv[1:] = ["project", "average_finding_age", "-c", "low", "-t", "FOO AND FIRSTTAG", "--output", "./tmp"]
    args, _ = fetch_args()
    expected = {"command": "project", "subcommand": "average_finding_age", "debug": False, "dryrun": False, "to_config": False, "output": "./tmp", "min_crit": "low", "from_tag": "FOO AND FIRSTTAG", "exclude_classifier": None, "shallow":False}
    assert convert_args_to_dict(args) == expected

    sys.argv[1:] = ["notification", "assign_projects", "-n", "team-test-mail", "-t", "SECONDTAG", "FIRSTTAG"]
    args, _ = fetch_args()
    expected = {"command": "notification", "subcommand": "assign_projects", "debug": False, "dryrun": False, "to_config": False, "output": None, "from_tag": ["SECONDTAG", "FIRSTTAG"], "rule_name": "team-test-mail", "force": False}
    assert convert_args_to_dict(args) == expected

def test_convert_cli_to_config():
    sys.argv[1:] = ["project", "analyze_vulnerabilities", "-c", "low", "-t", "FIRSTTAG"]
    args, _ = fetch_args()
    expected = "[[toolkit.project.analyze_vulnerabilities]]\ntitle='newtask'\ndebug=false\ndryrun=false\nmin_crit='low'\nfrom_tag='FIRSTTAG'\nshallow=false\n"
    assert convert_cli_to_config(args) == expected
    
    sys.argv[1:] = ["project", "average_finding_age", "-c", "low", "-t", "FIRSTTAG"]
    args, _ = fetch_args()
    expected = "[[toolkit.project.average_finding_age]]\ntitle='newtask'\ndebug=false\ndryrun=false\nmin_crit='low'\nfrom_tag='FIRSTTAG'\nshallow=false\n"
    assert convert_cli_to_config(args) == expected

    sys.argv[1:] = ["notification", "assign_projects", "-n", "team-test-mail", "-t", "SECONDTAG", "FIRSTTAG"]
    args, _ = fetch_args()
    expected = "[[toolkit.notification.assign_projects]]\ntitle='newtask'\ndebug=false\ndryrun=false\nfrom_tag=['SECONDTAG', 'FIRSTTAG']\nrule_name='team-test-mail'\n"
    assert convert_cli_to_config(args) == expected

