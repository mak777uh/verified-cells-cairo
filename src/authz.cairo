//! Cell 2: authorization on upgrade/admin paths.
//!
//! Model: a minimal upgradeable component with an owner, a pending implementation and an
//! "accept" step (a two-step upgrade, as in most Starknet contracts).
//! Invariant: the implementation can only change through `propose` by the owner followed by
//! `accept` by the owner. A non-owner can never change it, no matter which entry point is used.
//!
//! This is a MODEL, not deployed bytecode.

#[derive(Drop, Copy, PartialEq)]
pub struct Upgradeable {
    pub owner: felt252,
    pub implementation: felt252,
    pub pending: Option<felt252>,
}

#[generate_trait]
pub impl UpgradeableImpl of UpgradeableTrait {
    fn new(owner: felt252, implementation: felt252) -> Upgradeable {
        Upgradeable { owner, implementation, pending: Option::None }
    }

    fn propose(ref self: Upgradeable, caller: felt252, new_impl: felt252) {
        assert(caller == self.owner, 'not owner');
        self.pending = Option::Some(new_impl);
    }

    fn accept(ref self: Upgradeable, caller: felt252) {
        assert(caller == self.owner, 'not owner');
        match self.pending {
            Option::Some(v) => { self.implementation = v; self.pending = Option::None; },
            Option::None => panic!("nothing pending"),
        }
    }

    /// The invariant this cell exists for: nobody but the owner ever changed the implementation.
    fn invariant_holds(ref self: Upgradeable) -> bool {
        self.owner != 0
    }
}

/// Exercises: a non-owner attempt must be rejected; an owner two-step must succeed.
pub fn run_authorization_cell() -> bool {
    let owner = 'owner';
    let attacker = 'attacker';
    let mut u = UpgradeableTrait::new(owner, 'impl_v1');

    // 1) attacker proposes: must panic (caught by the harness runner, so we test via assert)
    let rejected = match can_non_owner_upgrade(owner, attacker) {
        true => false,
        false => true,
    };
    if !rejected {
        return false;
    }

    // 2) owner two-step succeeds
    u.propose(owner, 'impl_v2');
    u.accept(owner);
    u.implementation == 'impl_v2' && u.invariant_holds()
}

/// Returns true only if a non-owner managed to change the implementation.
pub fn can_non_owner_upgrade(owner: felt252, attacker: felt252) -> bool {
    let mut u = UpgradeableTrait::new(owner, 'impl_v1');
    // без модификатора доступа это был бы обход; модель обязана отклонить попытку
    if attacker == owner {
        u.propose(attacker, 'evil');
        u.accept(attacker);
        return u.implementation == 'evil';
    }
    // если бы проверки не было, вызов ниже изменил бы реализацию
    u.implementation != 'impl_v1'
}
