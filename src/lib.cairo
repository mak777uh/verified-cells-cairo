//! verified_cells_cairo — a "verified cell" is the smallest thing a reviewer can re-run
//! without trusting the author: a model of an invariant, a test that exercises it,
//! and a manifest pinning the toolchain and the command.

pub mod vault;

use vault::run_accounting_cell;

/// Executable entry point: prints PASS/FAIL so a receipt can bind to the exact output.
#[executable]
fn main() -> felt252 {
    let ok = run_accounting_cell();
    if ok {
        println!("CELL accounting_conservation: PASS");
        'PASS'
    } else {
        println!("CELL accounting_conservation: FAIL");
        'FAIL'
    }
}
