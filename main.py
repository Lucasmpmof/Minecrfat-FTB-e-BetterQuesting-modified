import argparse
import logging

from actions.scan import scan
from actions.analyze import analyze
from actions.edit_test import edit_test
from actions.remove_mod import remove_mod
from actions.validate import validate
from actions.clean import clean
from actions.modpack_profile import modpack_profile
from actions.progression import progression


def main():
    
    parser = argparse.ArgumentParser(

        description="Questbook Toolkit"

    )


    subparsers = parser.add_subparsers(

        dest="command",

        required=True

    )


    #
    # SCAN
    #

    scan_parser = subparsers.add_parser(
        "scan"
    )


    scan_parser.add_argument(
        "--questbook",
        required=True
    )


    scan_parser.add_argument(
        "--debug",
        action="store_true"
    )


    scan_parser.add_argument(
        "--report"
    )



    #
    # ANALYZE
    #

    analyze_parser = subparsers.add_parser(
        "analyze"
    )


    analyze_parser.add_argument(
        "--questbook",
        required=True
    )


    analyze_parser.add_argument(
        "--output",
        help="Arquivo JSON"
    )



    #
    # EDIT TEST
    #

    edit_parser = subparsers.add_parser(
        "edit-test"
    )


    edit_parser.add_argument(
        "--questbook",
        required=True
    )



    #
    # REMOVE MOD
    #

    remove_parser = subparsers.add_parser(
        "remove-mod"
    )


    remove_parser.add_argument(
        "--questbook",
        required=True
    )


    remove_parser.add_argument(
        "--mod",
        required=True
    )


    remove_parser.add_argument(
        "--output",
        required=True
    )


    remove_parser.add_argument(
        "--dry-run",
        action="store_true"
    )



    #
    # VALIDATE
    #

    validate_parser = subparsers.add_parser(
        "validate"
    )


    validate_parser.add_argument(
        "--questbook",
        required=True
    )
    validate_parser.add_argument(
        "--json",
        help="Salvar relatório JSON"
    )
    clean_parser = subparsers.add_parser(
        "clean"
    )
    #
    # CLEAN
    #

    clean_parser.add_argument(
        "--questbook",
        required=True
    )


    clean_parser.add_argument(
        "--output",
        required=True
    )

    #
    # MODPACK PROFILE
    #

    modpack_parser = subparsers.add_parser(
        "modpack-profile"
    )

    modpack_parser.add_argument(
        "--questbook",
        required=True
    )

    modpack_parser.add_argument(
        "--mods",
        required=True,
        help="Pasta mods/ da instância Minecraft"
    )

    modpack_parser.add_argument(
        "--output",
        help="Obrigatório fora do modo --dry-run"
    )

    modpack_parser.add_argument(
        "--dry-run",
        action="store_true"
    )

    modpack_parser.add_argument(
        "--report",
        help="Salvar relatório JSON"
    )

    #
    # PROGRESSION
    #

    progression_parser = subparsers.add_parser(
        "progression"
    )

    progression_parser.add_argument(
        "--questbook",
        required=True
    )

    progression_parser.add_argument(
        "--export-clusters",
        help=(
            "Exporta ProgressionClusters + ClusterGraph para um "
            "arquivo JSON (ex.: clusters.json)"
        )
    )

    args = parser.parse_args()



    logging.basicConfig(

        level=logging.INFO,

        format="%(levelname)s: %(message)s"

    )

    #
    # EXECUÇÃO
    #
    if args.command == "scan":


        scan(

            folder=args.questbook,

            debug=args.debug,

            report_file=args.report

        )

    elif args.command == "analyze":


        analyze(

            folder=args.questbook,

            output=args.output

        )



    elif args.command == "edit-test":


        edit_test(

            folder=args.questbook

        )



    elif args.command == "remove-mod":


        remove_mod(

            folder=args.questbook,

            mod=args.mod,

            output=args.output,

            dry_run=args.dry_run

        )



    elif args.command == "validate":


        validate(
            folder=args.questbook,
            json_output=args.json
        )
    elif args.command == "clean":

        clean(
            folder=args.questbook,
            output=args.output
        )

    elif args.command == "modpack-profile":

        modpack_profile(
            folder=args.questbook,
            mods_folder=args.mods,
            output=args.output,
            dry_run=args.dry_run,
            report_file=args.report
        )

    elif args.command == "progression":

        progression(
            folder=args.questbook,
            export_clusters_file=args.export_clusters
        )

if __name__ == "__main__":

    main()