from argparse import ArgumentParser

from core.cli_service import CLIService
from core.file_service import FileService


def run():
    file_srv = FileService()
    cli_service = CLIService()


    parser = ArgumentParser(description='Sample and run configuration')
    parser.add_argument('-s', '--sample', type=int, help='number of configuration to sample & run')
    parser.add_argument('-d', '--data', type=str, required=True,
                        help='path to data descriptor JSON')
    parser.add_argument('-m', '--mean', action='store_true', help='generate mean nifti image of all results and correlations from it')
    parser.add_argument('-r', '--ref', action='store_true', help='generate correlations from reference result')
    parser.add_argument('-c', '--correlations', action='store_true', help='generate all correlations between results')
    parser.add_argument('-e', '--execute', type=str, help='execute given configuration')

    args = parser.parse_args()
    data_desc = file_srv.read_data_descriptor(args.data)

    if args.sample is not None:
        cli_service.sample_run(data_desc, args.sample)
    if args.mean:
        cli_service.mean(data_desc)
    if args.ref:
        cli_service.ref(data_desc)
    if args.correlations:
        cli_service.correlations(data_desc)


if __name__ == '__main__':
    run()
