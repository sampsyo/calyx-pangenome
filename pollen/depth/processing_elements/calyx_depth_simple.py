from calyx.py_ast import *

def node_depth_pe(max_steps, max_paths):
    
    stdlib = Stdlib()
    
    # Variable identifiers

    # Input and Output ports
    depth_in = CompVar('depth_in')
    depth_write_en = CompVar('depth_write_en')
    depth_out = CompVar('depth_out')
    depth_done = CompVar('depth_done')
    uniq_in = CompVar('uniq_in')
    uniq_write_en = CompVar('uniq_write_en')
    uniq_out = CompVar('uniq_out')
    uniq_done = CompVar('uniq_done')
    # path_id for each step on the node
    pids_addr0 = CompVar('pids_addr0')    
    pids_read_data = CompVar('pids_read_data')
    # paths to consider
    ptc_addr0 = CompVar('ptc_addr0')
    ptc_read_data = CompVar('ptc_read_data')
    # paths on node
    pon_addr0 = CompVar('pon_addr0')
    pon_write_data = CompVar('pon_write_data')
    pon_write_en = CompVar('pon_write_en')
    pon_read_data = CompVar('pon_read_data')
    pon_done = CompVar('pon_done')
    
    path_id_reg = CompVar('path_id_reg')
    idx = CompVar('idx')
    idx_adder = CompVar('idx_adder')
    idx_neq = CompVar('idx_neq')
    
    depth_temp = CompVar('depth_temp')
    depth_pad = CompVar('depth_pad')
    depth_adder = CompVar('depth_adder')
    
    uniq_and = CompVar('uniq_and')
    uniq_and_reg_l = CompVar('uniq_and_reg_l')
    uniq_and_reg_r = CompVar('uniq_and_reg_r')
    uniq_pad = CompVar('uniq_pad')
    uniq_adder = CompVar('uniq_adder')
    
    uniq_idx = CompVar('uniq_idx')
    uniq_idx_neq = CompVar('uniq_idx_neq')
    uniq_idx_adder = CompVar('uniq_idx_adder')
    
    
    # Initialize the cells
    ptc_size = max_paths + 1
    path_id_width = max_paths.bit_length()
    depth_width = max_steps.bit_length() # number of bits to represent depth
    steps_width = max(1, (max_steps - 1).bit_length())
    uniq_width = path_id_width # number of bits to represent uniq depth
    
    cells = [

        # Idx cells
        Cell(idx, stdlib.register(steps_width)),
        Cell(idx_adder, stdlib.op("add", steps_width, signed=False)),
        Cell(idx_neq, stdlib.op("neq", steps_width, signed=False)),

        # Registers
        Cell(path_id_reg, stdlib.register(path_id_width)),
        Cell(uniq_and_reg_l, stdlib.register(1)),
        Cell(uniq_and_reg_r, stdlib.register(1)),
        
        # Cells for node depth computation
        Cell(depth_temp, stdlib.register(1)),
        Cell(depth_pad, stdlib.pad(1, depth_width)),
        Cell(depth_adder, stdlib.op("add", depth_width, signed=False)),
        
        # Cells for uniq node depth computation
        Cell(uniq_and, stdlib.op("and", 1, signed=False)),
        Cell(uniq_pad, stdlib.pad(1, uniq_width)),
        Cell(uniq_adder, stdlib.op("add", uniq_width, signed=False)),

        Cell(uniq_idx, stdlib.register(path_id_width)),
        Cell(uniq_idx_neq, stdlib.op("neq", path_id_width, signed=False)),
        Cell(uniq_idx_adder, stdlib.op("sub", path_id_width, signed=False)),
]

    
    # Initialize the wires
    wires = [
        Group(
            CompVar("init_idx"),
            [
                Connect(CompPort(idx, "in"), ConstantPort(steps_width, 0)),
                Connect(CompPort(idx, "write_en"), ConstantPort(1, 1)),
                Connect(
                    HolePort(CompVar("init_idx"), "done"),
                    CompPort(idx, "done")
                )
            ]
        ),
        
        Group(
            CompVar("load_path_id"),
            [
                Connect(ThisPort(pids_addr0), CompPort(idx, "out")),
                Connect(
                    CompPort(path_id_reg, "in"),
                    ThisPort(pids_read_data)
                ),
                Connect(CompPort(path_id_reg, "write_en"), ConstantPort(1,1)),
                Connect(
                    HolePort(CompVar("load_path_id"), "done"),
                    CompPort(path_id_reg, "done")
                ),
            ]
        ),
            
        Group(
            CompVar("inc_idx"),
            [
                Connect(CompPort(idx_adder, "left"), CompPort(idx, "out")),
                Connect(
                    CompPort(idx_adder, "right"),
                    ConstantPort(steps_width, 1)),
                Connect(CompPort(idx, "in"), CompPort(idx_adder, "out")),
                Connect(CompPort(idx, "write_en"), ConstantPort(1, 1)),
                Connect(
                    HolePort(CompVar("inc_idx"), "done"),
                    CompPort(idx, "done")
                )
            ]
        ),

        CombGroup(
            CompVar("compare_idx"),
            [
                Connect(CompPort(idx_neq, "left"), CompPort(idx, "out")),
                Connect(CompPort(idx_neq, "right"), ConstantPort(steps_width, max_steps - 1))
            ]
        ),

        # Node depth wires
        Group(
            CompVar("load_consider_path"),
            [
                Connect(
                    ThisPort(ptc_addr0),
                    CompPort(path_id_reg, "out")
                ),
                Connect(
                    CompPort(depth_temp, "in"),
                    ThisPort(ptc_read_data)
                ),
                Connect(CompPort(depth_temp, "write_en"), ConstantPort(1, 1)),
                Connect(
                    HolePort(CompVar("load_consider_path"), "done"),
                    CompPort(depth_temp, "done")
                )
            ]
        ),
            
        Group(
            CompVar("inc_depth"),
            [
                #If path_id is not 0, add 1 to depth
                Connect(CompPort(depth_adder, "left"), ThisPort(depth_out)),
                Connect(
                    CompPort(depth_pad, 'in'),
                    CompPort(depth_temp, 'out')
                ),
                Connect(
                    CompPort(depth_adder, "right"),
                    CompPort(depth_pad, 'out')
                ),
                Connect(ThisPort(depth_in), CompPort(depth_adder, "out")),
                Connect(ThisPort(depth_write_en), ConstantPort(1, 1)),
                Connect(
                    HolePort(CompVar("inc_depth"), "done"),
                    ThisPort(depth_done)
                )
            ]
        ),

        # Uniq node depth wires
        Group(
            CompVar('init_uniq_idx'),
            [
                Connect(
                    CompPort(uniq_idx, 'in'),
                    ConstantPort(uniq_width, max_paths)
                ),
                Connect(CompPort(uniq_idx, 'write_en'), ConstantPort(1, 1)),
                Connect(
                    HolePort(CompVar('init_uniq_idx'), 'done'),
                    CompPort(uniq_idx, 'done')
                )
            ]
        ),

        CombGroup(
            CompVar('compare_uniq_idx'),
            [
                Connect(
                    CompPort(uniq_idx_neq, 'left'),
                    CompPort(uniq_idx, 'out')
                ),
                Connect(
                    CompPort(uniq_idx_neq, 'right'),
                    ConstantPort(path_id_width, 0)
                )
            ]
        ),
        
        Group(
            CompVar('dec_uniq_idx'),
            [
                Connect(
                    CompPort(uniq_idx_adder, 'left'),
                    CompPort(uniq_idx, 'out')
                ),
                Connect(
                    CompPort(uniq_idx_adder, 'right'),
                    ConstantPort(path_id_width, 1)
                ),
                Connect(
                    CompPort(uniq_idx, 'in'),
                    CompPort(uniq_idx_adder, 'out')
                ),
                Connect(
                    CompPort(uniq_idx, 'write_en'),
                    ConstantPort(1, 1)
                ),
                Connect(
                    HolePort(CompVar('dec_uniq_idx'), 'done'),
                    CompPort(uniq_idx, 'done')
                )
            ]
        ),

        
        Group(
            CompVar('update_pon'), # update paths_on_node
            [
                Connect(
                    ThisPort(pon_addr0),
                    CompPort(path_id_reg, "out")
                ),
                Connect(
                    ThisPort(pon_write_data),
                    ConstantPort(1, 1)
                ),
                Connect(
                    ThisPort(pon_write_en),
                    ConstantPort(1, 1)
                ),
                Connect(
                    HolePort(CompVar("update_pon"), "done"),
                    ThisPort(pon_done)
                )
            ]
        ),

        Group(
            CompVar("load_and_l"),
            [
                Connect(
                    ThisPort(pon_addr0),
                    CompPort(uniq_idx, "out")
                ),
                Connect(
                    CompPort(uniq_and_reg_l, "in"),
                    ThisPort(pon_read_data)
                ),
                Connect(
                    CompPort(uniq_and_reg_l, "write_en"),
                    ConstantPort(1, 1)
                ),
                Connect(
                    HolePort(CompVar("load_and_l"), "done"),
                    CompPort(uniq_and_reg_l, "done")
                )
            ]
        ),

        Group(
            CompVar("load_and_r"),
            [
                Connect(
                    ThisPort(ptc_addr0),
                    CompPort(uniq_idx, "out")
                ),
                Connect(
                    CompPort(uniq_and_reg_r, "in"),
                    ThisPort(ptc_read_data)
                ),
                Connect(
                    CompPort(uniq_and_reg_r, "write_en"),
                    ConstantPort(1, 1)
                ),
                Connect(
                    HolePort(CompVar("load_and_r"), "done"),
                    CompPort(uniq_and_reg_r, "done")
                )   
            ]
        ),

        Group(
            CompVar("inc_uniq"),
            [
                Connect(
                    CompPort(uniq_and, "left"),
                    CompPort(uniq_and_reg_l, "out")
                ),
                Connect(
                    CompPort(uniq_and, "right"),
                    CompPort(uniq_and_reg_r, "out")
                ),
                Connect(CompPort(uniq_adder, "left"), ThisPort(uniq_out)),
                Connect(CompPort(uniq_pad, 'in'), CompPort(uniq_and, 'out')),
                Connect(
                    CompPort(uniq_adder, "right"),
                    CompPort(uniq_pad, 'out')
                ),
                Connect(ThisPort(uniq_in), CompPort(uniq_adder, "out")),
                Connect(ThisPort(uniq_write_en), ConstantPort(1, 1)),
                Connect(
                    HolePort(CompVar("inc_uniq"), "done"),
                    ThisPort(uniq_done)
                )
            ]
        ),
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
    ])
                        

    pe_component = Component(
        name="node_depth_pe",
        inputs=[
            PortDef(depth_out, depth_width), PortDef(depth_done, 1),
            PortDef(uniq_out, uniq_width), PortDef(uniq_done, 1),
            PortDef(pids_read_data, path_id_width),
            PortDef(ptc_read_data, 1),
            PortDef(pon_read_data, 1), PortDef(pon_done, 1)
        ],
        outputs=[
            PortDef(depth_in, depth_width), PortDef(depth_write_en, 1),
            PortDef(uniq_in, uniq_width), PortDef(uniq_write_en, 1),
            PortDef(pids_addr0, steps_width),
            PortDef(ptc_addr0, path_id_width),
            PortDef(pon_addr0, path_id_width), PortDef(pon_write_data, 1),
            PortDef(pon_write_en, 1)
        ],
        structs=cells + wires,
        controls=controls,
    )

    return pe_component