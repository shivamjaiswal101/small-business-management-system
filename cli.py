"""Small command-line interface for changing database configuration."""

import argparse
import sys

import business
import services


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description="Business Manager configuration commands")
    commands = parser.add_subparsers(dest="entity", required=True)

    business_parser = commands.add_parser("business", help="view or update the business")
    business_commands = business_parser.add_subparsers(dest="action")
    set_parser = business_commands.add_parser("set", help="set the business name")
    set_parser.add_argument("name")

    service_parser = commands.add_parser("service", help="manage business services")
    service_commands = service_parser.add_subparsers(dest="action", required=True)
    add_parser = service_commands.add_parser("add", help="add a service")
    add_parser.add_argument("name")
    service_commands.add_parser("list", help="list services")
    edit_parser = service_commands.add_parser("edit", help="rename a service")
    edit_parser.add_argument("id", type=int)
    edit_parser.add_argument("name")
    for action, help_text in (("remove", "deactivate a service"), ("activate", "activate a service")):
        command = service_commands.add_parser(action, help=help_text)
        command.add_argument("id", type=int)
    return parser


def run_cli(argv: list[str]) -> int:
    args = build_parser().parse_args(argv)
    try:
        configured_business = business.get_business()
        if args.entity == "business":
            if args.action == "set":
                result = business.set_business(args.name)
                print(f"Business set to: {result['name']}")
            elif configured_business:
                print(f"{configured_business['name']} (ID: {configured_business['id']})")
            else:
                print("Business setup has not been completed.")
            return 0

        if not configured_business:
            raise ValueError("Set up a business before managing services.")
        business_id = configured_business["id"]
        if args.action == "add":
            item = services.add_service(business_id, args.name)
            print(f"Added service {item['id']}: {item['name']}")
        elif args.action == "list":
            items = services.list_services(business_id, include_inactive=True)
            if not items:
                print("No services configured.")
            for item in items:
                state = "active" if item["active"] else "inactive"
                print(f"{item['id']}: {item['name']} ({state})")
        elif args.action == "edit":
            item = services.edit_service(business_id, args.id, args.name)
            print(f"Service {item['id']} renamed to: {item['name']}")
        elif args.action == "remove":
            item = services.deactivate_service(business_id, args.id)
            print(f"Deactivated service {item['id']}: {item['name']}")
        elif args.action == "activate":
            item = services.activate_service(business_id, args.id)
            print(f"Activated service {item['id']}: {item['name']}")
        return 0
    except ValueError as error:
        print(f"Error: {error}", file=sys.stderr)
        return 2
