//! Cell 3: idempotency of cross-contract calls.
//!
//! Model: an outbox that credits a recipient once per message id. A relayer may deliver the same
//! message twice (retries, reorgs, duplicate signatures); the effect must be applied exactly once.
//! Invariant: after any number of deliveries of the same id, `credited` grows by the amount once.
//!
//! The model uses two explicit flags instead of a dictionary on purpose: a cell should be readable
//! and deterministic, and two ids are enough to show "same id is a no-op, new id still works".
//!
//! This is a MODEL, not deployed bytecode.

#[derive(Drop, Copy, PartialEq)]
pub struct Outbox {
    pub processed_a: bool,
    pub processed_b: bool,
    pub credited: u256,
}

#[generate_trait]
pub impl OutboxImpl of OutboxTrait {
    fn new() -> Outbox {
        Outbox { processed_a: false, processed_b: false, credited: 0 }
    }

    /// Deliver message `id` (`'msg_a'` or `'msg_b'`).
    /// Returns true when the effect was applied, false when the delivery was a no-op.
    fn deliver(ref self: Outbox, id: felt252, amount: u256) -> bool {
        if id == 'msg_a' {
            if self.processed_a {
                return false;
            }
            self.processed_a = true;
            self.credited = self.credited + amount;
            return true;
        }
        if id == 'msg_b' {
            if self.processed_b {
                return false;
            }
            self.processed_b = true;
            self.credited = self.credited + amount;
            return true;
        }
        false
    }
}

/// Exercises: three deliveries of the same id, then one of a different id.
pub fn run_idempotency_cell() -> bool {
    let amount = 100_u256;
    let mut box = OutboxTrait::new();

    let first = box.deliver('msg_a', amount);
    let second = box.deliver('msg_a', amount);
    let third = box.deliver('msg_a', amount);
    let other = box.deliver('msg_b', amount);

    // 1) применилась только первая доставка одного и того же id
    let single_apply = first && !second && !third;
    // 2) новый id всё ещё работает — счётчик не «залип»
    let new_id_works = other;
    // 3) ровно две применённых доставки по 100
    let total_correct = box.credited == 200_u256;

    single_apply && new_id_works && total_correct
}
