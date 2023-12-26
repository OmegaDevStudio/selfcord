from __future__ import annotations
from typing import Self, Type


class Flags:
    def __init__(self, value: int):
        self.value: int = value

    @classmethod
    def from_value(cls, value: int):
        self = cls(value)
        self.value = value
        return self

    def __repr__(self) -> str:
        return f"{self.value}"


class Capabilities(Flags):
    
    @classmethod
    def default(cls):
        """Utilise default values for optimal anti-flag"""
        # Discum uses 4093
        # Desktop client uses 16381
        # Discord.py-self uses 8189
        return cls.from_value(8189)

    @classmethod
    def lazy_user_notes(cls: Type[Self]) -> Self:
        """Disable preloading of user notes in READY."""
        return cls.from_value(1 << 0)

    @classmethod
    def no_affine_user_ids(cls: Type[Self]) -> Self:
        """Disable implicit relationship updates."""
        return cls.from_value(1 << 1)

    @classmethod
    def versioned_read_states(cls: Type[Self]) -> Self:
        """Enable versioned read states (change READY ``read_state`` to an object with ``version``/``partial``)."""
        return cls.from_value(1 << 2)

    @classmethod
    def versioned_user_guild_settings(cls: Type[Self]) -> Self:
        """Enable versioned user guild settings (change READY ``user_guild_settings`` to an object with ``version``/``partial``)."""
        return cls.from_value(1 << 3)

    @classmethod
    def dedupe_user_objects(cls: Type[Self]) -> Self:
        """Enable dehydration of the READY payload (move all user objects to a ``users`` array and replace them in various places in the READY payload with ``user_id`` or ``recipient_id``, move member object(s) from initial guild objects to ``merged_members``)."""
        return cls.from_value(1 << 4)

    @classmethod
    def prioritized_ready_payload(cls: Type[Self]) -> Self:
        """Enable prioritized READY payload (enable READY_SUPPLEMENTAL, move ``voice_states`` and ``embedded_activities`` from initial guild objects and ``merged_presences`` from READY, as well as split ``merged_members`` and (sometimes) ``private_channels``/``lazy_private_channels`` between the events)."""
        # Requires self.dedupe_user_objects
        return cls.from_value(1 << 5 | 1 << 4)

    @classmethod
    def multiple_guild_experiment_populations(cls: Type[Self]) -> Self:
        """Handle multiple guild experiment populations (change the fourth entry of arrays in the ``guild_experiments`` array in READY to have an array of population arrays)."""
        return cls.from_value(1 << 6)

    @classmethod
    def non_channel_read_states(cls: Type[Self]) -> Self:
        """Handle non-channel read states (change READY ``read_state`` to include read states tied to server events, server home, and the mobile notification center)."""
        return cls.from_value(1 << 7)

    @classmethod
    def auth_token_refresh(cls: Type[Self]) -> Self:
        """Enable auth token refresh (add ``auth_token?`` to READY; this is sent when Discord wants to change the client's token, and was used for the mfa. token migration)."""
        return cls.from_value(1 << 8)

    @classmethod
    def user_settings_proto(cls: Type[Self]) -> Self:
        """Disable legacy user settings (remove ``user_settings`` from READY and stop sending USER_SETTINGS_UPDATE)."""
        return cls.from_value(1 << 9)

    @classmethod
    def client_state_v2(cls: Type[Self]) -> Self:
        """Enable client caching v2 (move guild properties in guild objects to a ``properties`` subkey and add ``data_mode`` and ``version`` to the objects, as well as change ``client_state`` in IDENTIFY)."""
        return cls.from_value(1 << 10)

    @classmethod
    def passive_guild_update(cls: Type[Self]) -> Self:
        """Enable passive guild update (replace ``CHANNEL_UNREADS_UPDATE`` with ``PASSIVE_UPDATE_V1``, a similar event that includes a ``voice_states`` array and a ``members`` array that includes the members of aforementioned voice states)."""
        return cls.from_value(1 << 11)
