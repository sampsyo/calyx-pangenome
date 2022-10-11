'''
Combines the commandline interface for calyx_depth.py and parse_data.py. Run ./main.py -h for more info.
'''

import argparse
import json
import os.path
import subprocess

from . import calyx_depth as depth
from . import parse_data

def config_parser(parser):

    depth.config_parser(parser)    
    
    parser.add_argument(
        '--action',
        default='gen',
        help=
        """ 
        Specify the action to take:
            gen (default): generate an accelerator
            parse: parse the .og --file to accelerator input
            run: run node depth on the .og or .data --file. Outputs the node depth table by default.
        """
    )
    
    parser.add_argument(
        '-f',
        '--file',
        dest='filename',
        help='A .og or .data file. If --action=parse, this must be a .og file.'
    )
    parser.add_argument(
        '-s',
        '--subset-paths',
        help='Should only be set if the action is not gen. Specifies a\
 subset of paths whose node depth to compute.'
    )

    parser.add_argument(
        '-x',
        '--accelerator',
        help='Specify a node depth accelerator to run. Should only be set if action is run.'
    )
    parser.add_argument(
        '--pr',
        action='store_true',
        help='Print profiling info. Passes the -pr flag to fud if --run is set.'
    )
    

def run(args):
    
    if args.action == 'gen': # Generate an accelerator
        if args.filename or args.subset_paths or args.accelerator or args.pr:
            warnings.warn('--file, --subset-paths, --accelerator, and --pr will be ignored if action is gen.', SyntaxWarning)
            
        depth.run(args)
        return

    
    # Check for valid commandline input
    if not (args.action == 'parse' or args.action == 'run'):
        raise Exception('action should be gen, parse, or run')
        
    if not args.filename:
        raise Exception('--file must be provided when action is parse or run.')
    base, ext = os.path.splitext(args.filename)

    parser = argparse.ArgumentParser()
    parser.add_argument('--out')
    parser.add_argument('-v', '--from-verilog')
    parser.add_argument('-i', '--from-interp')    
    
    if args.action == 'parse': # Generate a data file
        if args.accelerator or args.pr:
            warnings.warn('--accelerator and --pr will be ignored if action is not run.', SyntaxWarning)

        parser.parse_args([], namespace=args)
        parse_data.run(args)
        
    elif args.action == 'run': # Run the accelerator

        # Parse the data file if necessary
        out_file = args.out
        _, ext = os.path.splitext(args.filename)
        
        if ext == '.data':
            data_file = args.filename
        else:
            data_file = 'tmp.data'
            parser.parse_args(['--out', data_file], namespace=args)
            parse_data.run(args)
        
        # Generate the accelerator if necessary
        if args.accelerator:
            futil_file = args.accelerator
        else:
            futil_file = 'tmp.futil'
            parser.parse_args(['--out', futil_file], namespace=args)
            depth.run(args)

        # Compute the node depth
        cmd = ['fud', 'e', futil_file, '--to', 'interpreter-out',
               '-s', 'verilog.data', data_file]
        if args.pr:
            cmd.append('-pr')
            calyx_out = subprocess.run(cmd, capture_output=True, text=True)
            output = calyx_out.stdout

        else:
            calyx_out = subprocess.run(cmd, capture_output=True, text=True)
            # Convert calyx output to a node depth table
            calyx_out = json.loads(calyx_out.stdout)
            output = parse_data.from_calyx(calyx_out, True) # ndt
        
        # Output the ndt
        if out_file:
            with open(out_file, 'w') as out_file:
                out_file.write(output)
        else:
            print(output)

        # Remove temporary files
        subprocess.run(['rm', 'tmp.data', 'tmp.futil'], capture_output=True)

        
def main():
    parser = argparse.ArgumentParser()
    
    config_parser(parser)

    args = parser.parse_args()
    run(args)

if __name__ == '__main__':
    main()
