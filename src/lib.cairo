//! verified_cells_cairo — a "verified cell" is the smallest thing a reviewer can re-run
//! without trusting the author: a model of an invariant, a test that exercises it,
//! and a manifest pinning the toolchain and the command.

pub mod vault;
pub mod authz;

use authz::run_authorization_cell;
use vault::run_accounting_cell;

/// Executable entry point: prints PASS/FAIL for every cell so a receipt binds to exact output.
#[executable]
fn main() -> felt252 {
    let mut failures = 0;
    if run_accounting_cell() {
        println!("CELL accounting_conservation: PASS");
    } else {
        println!("CELL accounting_conservation: FAIL");
        failures = failures + 1;
    };
    if run_authorization_cell() {
        println!("CELL authorization_on_upgrade: PASS");
    } else {
        println!("CELL authorization_on_upgrade: FAIL");
        failures = failures + 1;
    };
    if failures == 0 {
        'PASS'
    } else {
        'FAIL'
    }
}
