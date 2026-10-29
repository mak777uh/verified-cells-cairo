//! Cell 5: upgrade safety (storage slot preservation).
//!
//! Model: a two-version contract. v2 must keep every slot that v1 wrote at the same index;
//! otherwise an upgrade silently reinterprets old state.
//! Invariant: the slot map of v2 is a prefix-compatible extension of v1.
//!
//! This is a MODEL, not deployed bytecode.

#[derive(Drop, Copy, PartialEq)]
pub struct Layout {
    pub slot0: felt252, // owner
    pub slot1: felt252, // beneficiary
    pub slots_len: u32,
}

pub fn layout_v1() -> Layout {
    Layout { slot0: 'owner', slot1: 'beneficiary', slots_len: 2 }
}

/// v2 adds a field but must not reorder the first two slots.
pub fn layout_v2() -> (Layout, felt252) {
    (Layout { slot0: 'owner', slot1: 'beneficiary', slots_len: 3 }, 'fee_bps')
}

/// v2_broken swaps the order — this is the bug the cell is meant to catch.
pub fn layout_v2_broken() -> Layout {
    Layout { slot0: 'beneficiary', slot1: 'owner', slots_len: 3 }
}

pub fn run_upgrade_safety_cell() -> bool {
    let v1 = layout_v1();
    let (v2, _extra) = layout_v2();
    let broken = layout_v2_broken();

    let good = v2.slot0 == v1.slot0 && v2.slot1 == v1.slot1 && v2.slots_len >= v1.slots_len;
    let caught = !(broken.slot0 == v1.slot0 && broken.slot1 == v1.slot1);

    good && caught
}
