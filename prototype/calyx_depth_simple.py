from calyx.py_ast import *
import argparse
from parse_data import get_maxes


MAX_NODES=32
MAX_STEPS=15
MAX_PATHS=7

def node_depth(max_nodes=MAX_NODES, max_steps=MAX_STEPS, max_paths=MAX_PATHS):
    
    stdlib = Stdlib()
    
    # Variable identifiers
    path_ids = CompVar('path_ids') # path_id for each step on the node
    paths_to_consider = CompVar('paths_to_consider') 
    paths_on_node = CompVar('paths_on_node') # computed by depth.uniq
    depth_output = CompVar('depth_output')
    uniq_output = CompVar('uniq_output')
    
    path_id_reg = CompVar('path_id_reg')
    idx = CompVar('idx')
    idx_adder = CompVar('idx_adder')
    idx_neq = CompVar('idx_neq')
    
    depth = CompVar('depth')
    depth_temp = CompVar('depth_temp')
    depth_pad = CompVar('depth_pad')
    depth_adder = CompVar('depth_adder')
    
    uniq = CompVar('uniq')
    uniq_and = CompVar('uniq_and')
    uniq_and_reg_l = CompVar('uniq_and_reg_l')
    uniq_and_reg_r = CompVar('uniq_and_reg_r')
    uniq_pad = CompVar('uniq_pad')
    uniq_adder = CompVar('uniq_adder')
    
    uniq_idx = CompVar('uniq_idx')
    uniq_idx_neq = CompVar('unid_idx_neq')
    uniq_idx_adder = CompVar('uniq_idx_adder')
    

    # Initialize the cells
    ptc_size = max_paths + 1
    path_id_width = max_paths.bit_length()
    depth_width = max_steps.bit_length() # number of bits to represent depth
    steps_width = max(1, (max_steps - 1).bit_length())
    uniq_width = path_id_width # number of bits to represent uniq depth
    
    cells = [
        # Memory cells for path_ids and paths_on_node
        Cell(path_ids, stdlib.mem_d1(path_id_width, max_steps, steps_width), is_external=True),
        Cell(paths_to_consider, stdlib.mem_d1(1, ptc_size, path_id_width), is_external=True),
        Cell(paths_on_node, stdlib.mem_d1(1, ptc_size, path_id_width), is_external=True),
        Cell(depth_output, stdlib.mem_d1(depth_width, 1, 1), is_external=True),
        Cell(uniq_output, stdlib.mem_d1(uniq_width, 1, 1), is_external=True),

        # Idx cells
        Cell(idx, stdlib.register(steps_width)),
        Cell(idx_adder, stdlib.op("add", steps_width, signed=False)),
        Cell(idx_neq, stdlib.op("neq", steps_width, signed=False)),

        # Registers
        Cell(path_id_reg, stdlib.register(path_id_width)),
        Cell(uniq_and_reg_l, stdlib.register(1)),
        Cell(uniq_and_reg_r, stdlib.register(1)),
        
        # Cells for node depth computation
        Cell(depth, stdlib.register(depth_width)),
        Cell(depth_temp, stdlib.register(1)),
        Cell(depth_pad, stdlib.pad(1, depth_width)),
        Cell(depth_adder, stdlib.op("add", depth_width, signed=False)),
        
        # Cells for uniq node depth computation
        Cell(uniq, stdlib.register(uniq_width)),
        Cell(uniq_and, stdlib.op("and", 1, signed=False)),
        Cell(uniq_pad, stdlib.pad(1, uniq_width)),
        Cell(uniq_adder, stdlib.op("add", uniq_width, signed=False)),

        Cell(uniq_idx, stdlib.register(path_id_width)),
        Cell(uniq_idx_neq, stdlib.op("neq", path_id_width, signed=False)),
        Cell(uniq_idx_adder, stdlib.op("sub", path_id_width, signed=False))
    ]

    
    # Initialize the wires
    wires = [
        Group(
            CompVar("init_idx"),
            [
                Connect(ConstantPort(steps_width, 0), CompPort(idx, "in")),
                Connect(ConstantPort(1, 1), CompPort(idx, "write_en")),
                Connect(CompPort(idx, "done"), HolePort(CompVar("init_idx"), "done"))
            ]
        ),
        
        Group(
            CompVar("load_path_id"),
            [
                Connect(CompPort(idx, "out"), CompPort(path_ids, "addr0")),
                Connect(CompPort(path_ids, "read_data"), CompPort(path_id_reg, "in")),
                Connect(ConstantPort(1,1), CompPort(path_id_reg, "write_en")),
                Connect(CompPort(path_id_reg, "done"), HolePort(CompVar("load_path_id"), "done")),
            ]
        ),
            
        Group(
            CompVar("inc_idx"),
            [
                Connect(CompPort(idx, "out"), CompPort(idx_adder, "left")),
                Connect(ConstantPort(steps_width, 1), CompPort(idx_adder, "right")),
                Connect(CompPort(idx_adder, "out"), CompPort(idx, "in")),
                Connect(ConstantPort(1, 1), CompPort(idx, "write_en")),
                Connect(CompPort(idx, "done"), HolePort(CompVar("inc_idx"), "done"))
            ]
        ),

        CombGroup(
            CompVar("compare_idx"),
            [
                Connect(CompPort(idx, "out"), CompPort(idx_neq, "left")),
                Connect(ConstantPort(steps_width, max_steps - 1), CompPort(idx_neq, "right"))
            ]
        ),

        # Node depth wires
        Group(
            CompVar("load_consider_path"),
            [
                Connect(CompPort(path_id_reg, "out"), CompPort(paths_to_consider, "addr0")),
                Connect(CompPort(paths_to_consider, "read_data"), CompPort(depth_temp, "in")),
                Connect(ConstantPort(1, 1), CompPort(depth_temp, "write_en")),
                Connect(CompPort(depth_temp, "done"), HolePort(CompVar("load_consider_path"), "done"))
            ]
        ),
            
        Group(
            CompVar("inc_depth"),
            [
                #If path_id is not 0, add 1 to depth
                Connect(CompPort(depth, "out"), CompPort(depth_adder, "left")),
                Connect(CompPort(depth_temp, 'out'), CompPort(depth_pad, 'in')),
                Connect(CompPort(depth_pad, 'out'), CompPort(depth_adder, "right")),
                Connect(CompPort(depth_adder, "out"), CompPort(depth, "in")),
                Connect(ConstantPort(1, 1), CompPort(depth, "write_en")),
                Connect(CompPort(depth, "done"), HolePort(CompVar("inc_depth"), "done"))
            ]
        ),

        Group(
            CompVar('write_depth'),
            [
                Connect(ConstantPort(1, 0), CompPort(depth_output, "addr0")),
                Connect(CompPort(depth, 'out'), CompPort(depth_output, 'write_data')),
                Connect(ConstantPort(1, 1), CompPort(depth_output, 'write_en')),
                Connect(CompPort(depth_output, 'done'), HolePort(CompVar('write_depth'), 'done'))
            ]
        ),


        # Uniq node depth wires
        Group(
            CompVar('init_uniq_idx'),
            [
                Connect(ConstantPort(uniq_width, max_paths), CompPort(uniq_idx, 'in')),
                Connect(ConstantPort(1, 1), CompPort(uniq_idx, 'write_en')),
                Connect(CompPort(uniq_idx, 'done'), HolePort(CompVar('init_uniq_idx'), 'done'))
            ]
        ),

        CombGroup(
            CompVar('compare_uniq_idx'),
            [
                Connect(CompPort(uniq_idx, 'out'), CompPort(uniq_idx_neq, 'left')),
                Connect(ConstantPort(path_id_width, 0), CompPort(uniq_idx_neq, 'right'))
            ]
        ),
        
        Group(
            CompVar('dec_uniq_idx'),
            [
                Connect(CompPort(uniq_idx, 'out'), CompPort(uniq_idx_adder, 'left')),
                Connect(ConstantPort(path_id_width, 1), CompPort(uniq_idx_adder, 'right')),
                Connect(CompPort(uniq_idx_adder, 'out'), CompPort(uniq_idx, 'in')),
                Connect(ConstantPort(1, 1), CompPort(uniq_idx, 'write_en')),
                Connect(CompPort(uniq_idx, 'done'), HolePort(CompVar('dec_uniq_idx'), 'done'))
            ]
        ),

        
        Group(
            CompVar('update_pon'), # update paths_on_node
            [
                Connect(CompPort(path_id_reg, "out"), CompPort(paths_on_node, "addr0")),
                Connect(ConstantPort(1, 1), CompPort(paths_on_node, "write_data")),
                Connect(ConstantPort(1, 1), CompPort(paths_on_node, "write_en")),
                Connect(CompPort(paths_on_node, "done"), HolePort(CompVar("update_pon"), "done"))
            ]
        ),

        Group(
            CompVar("load_and_l"),
            [
                Connect(CompPort(uniq_idx, "out"), CompPort(paths_on_node, "addr0")),
                Connect(CompPort(paths_on_node, "read_data"), CompPort(uniq_and_reg_l, "in")),
                Connect(ConstantPort(1, 1), CompPort(uniq_and_reg_l, "write_en")),
                Connect(CompPort(uniq_and_reg_l, "done"), HolePort(CompVar("load_and_l"), "done"))
            ]
        ),

        Group(
            CompVar("load_and_r"),
            [
                Connect(CompPort(uniq_idx, "out"), CompPort(paths_to_consider, "addr0")),
                Connect(CompPort(paths_to_consider, "read_data"), CompPort(uniq_and_reg_r, "in")),
                Connect(ConstantPort(1, 1), CompPort(uniq_and_reg_r, "write_en")),
                Connect(CompPort(uniq_and_reg_r, "done"), HolePort(CompVar("load_and_r"), "done"))            
            ]
        ),

        Group(
            CompVar("inc_uniq"),
            [
                Connect(CompPort(uniq_and_reg_l, "out"), CompPort(uniq_and, "left")),
                Connect(CompPort(uniq_and_reg_r, "out"), CompPort(uniq_and, "right")),          
                Connect(CompPort(uniq, "out"), CompPort(uniq_adder, "left")),
                Connect(CompPort(uniq_and, 'out'), CompPort(uniq_pad, 'in')),
                Connect(CompPort(uniq_pad, 'out'), CompPort(uniq_adder, "right")),
                Connect(CompPort(uniq_adder, "out"), CompPort(uniq, "in")),
                Connect(ConstantPort(1, 1), CompPort(uniq, "write_en")),
                Connect(CompPort(uniq, "done"), HolePort(CompVar("inc_uniq"), "done"))
            ]
        ),

        Group(
            CompVar("store_uniq"),
            [
                Connect(ConstantPort(1, 0), CompPort(uniq_output, 'addr0')),
                Connect(CompPort(uniq, 'out'), CompPort(uniq_output, 'write_data')),
                Connect(ConstantPort(1, 1), CompPort(uniq_output, 'write_en')),
                Connect(CompPort(uniq_output, 'done'), HolePort(CompVar('store_uniq'), 'done'))
            ]
        )
    ]
    

    # Define control flow
    controls = SeqComp([
        Enable("init_idx"),
        ParComp([
            Enable('init_uniq_idx'),
            While(
                CompPort(idx_neq, "out"),
                CompVar("compare_idx"),
                SeqComp([
                    Enable("load_path_id"),
                    ParComp([
                        Enable('inc_idx'),
                        # Depth computation
                        SeqComp([
                            Enable("load_consider_path"),
                            Enable("inc_depth"),
                        ]),
                        # Uniq computation
                        Enable('update_pon')
                    ])
                ])
            )
        ]),
        Enable("load_path_id"),
        Enable("load_consider_path"),
        Enable("inc_depth"),
        Enable('write_depth'),
        Enable('update_pon'),
        While(
            CompPort(uniq_idx_neq, 'out'),
            CompVar('compare_uniq_idx'),
            SeqComp([
                ParComp([Enable('load_and_l'), Enable('load_and_r')]),
                Enable('inc_uniq'),
                Enable('dec_uniq_idx')    
            ])    
        ),
        Enable('store_uniq')
    ])
        
    # Node depth
    # Get the path_id
    # If path_id neq 0, add 1 to depth

    # Uniq node depth
    # For each step:
        # Get the path_id
        # set paths_on_node[node][path_id] to 1
    # sum paths_on_node[node] AND paths_to_consider
    
    # Control flow
    # In parallel: for each node
    # In parallel: compute node depth and uniq depth
        # Node depth sequence:
        #     1) Get path_id
        #     2) compute path_id neq 0
        #     3) add 1 to depth if path_id neq 0

        # Uniq depth sequence:
        # 
                        

    main_component = Component(
        name="main",
        inputs=[],
        outputs=[],
        structs=cells + wires,
        controls=controls,
    )

    # Create the Calyx program.
    program = Program(
        imports=[
            Import("primitives/core.futil"),
            Import("primitives/binary_operators.futil")
        ],
        components=[main_component]
    )

    return program
            
if __name__ == '__main__':

    # Parse commandline input
    parser = argparse.ArgumentParser()
    parser.add_argument('-a', '--auto-size', help='automatically infer the dimensions of the hardware accelerator')
    parser.add_argument('-n', '--max-nodes', type=int, default=MAX_NODES, help='Specify the maximum number of nodes that the hardware can support.')
    parser.add_argument('-e', '--max-steps', type=int, default=MAX_STEPS, help='Specify the maximum number of steps per node that the hardware can support.')
    parser.add_argument('-p', '--max-paths', type=int, default=MAX_PATHS, help='Specify the maximum number of paths that the hardware can support.')
    parser.add_argument('-o', '--out', help='Specify the output file. If not specified, will dump to stdout.')

    args = parser.parse_args()

    if args.auto_size:
        max_steps, max_paths = get_maxes(args.auto_size)
    else:
        max_steps, max_paths = args.max_steps, args.max_paths
        
    # Generate calyx code
    program = node_depth(max_steps=max_steps, max_paths=max_paths)

    # Emit the code
    if (args.out):
        with open(args.out, 'w') as out_file:
            out_file.write(program.doc())
    else:
        program.emit()            
