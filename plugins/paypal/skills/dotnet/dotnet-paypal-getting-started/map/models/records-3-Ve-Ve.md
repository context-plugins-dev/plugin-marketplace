# Records (`VenmoPaymentToken` … `VenmoWalletVaultAttributes`)

**Exact coverage: `VenmoPaymentToken` through `VenmoWalletVaultAttributes`**, alphabetical — these are the literal first and last record names on this page; a name outside that range is on a neighbouring page.

Plain `record` data models (immutable, `init`-only). Each field is `CSharpName (wire_name): Type` —
the parenthesized name is the JSON wire name (`[JsonPropertyName]`). `!req` = C# `required` (must be
set in the object initializer); a trailing `?` on the type = nullable/optional; a field with neither
is optional with a generated default — where the source declares an explicit default it is shown as
`= value`. Summary is the record's XML doc summary (`—` when the source has none). Error-payload
models (the `out` types named by the operation pages' error accessors) are listed here like any
other record. A field whose type is a `OneOf`/`AnyOf` union is tagged `(union)` — construct and
read it via `unions.md` (factories + `TryGet…`), not as a record.
All records on these pages live in namespace `PayPalServerSdk.Models`.

| Record | Summary | Fields | Source |
|---|---|---|---|
| `VenmoPaymentToken` | Full representation of a Venmo Payment Token. | `Description (description): string?`, `UsagePattern (usage_pattern): UsagePattern?`, `Shipping (shipping): VaultedDigitalWalletShippingDetails?`, `PermitMultiplePaymentTokens (permit_multiple_payment_tokens): bool? = false`, `UsageType (usage_type): PayPalPaymentTokenUsageType?`, `CustomerType (customer_type): PayPalPaymentTokenCustomerType?`, `EmailAddress (email_address): string?`, `PayerId (payer_id): string?`, `Name (name): Name?`, `Phone (phone): PhoneWithType?`, `Address (address): Address?`, `UserName (user_name): string?` | `Models/VenmoPaymentToken.cs` |
| `VenmoVaultResponse` | The details about a saved venmo payment source. | `Id (id): string?`, `Status (status): VenmoVaultResponseStatus?`, `Links (links): IReadOnlyList<LinkDescription>?`, `Customer (customer): CustomerInformation?` | `Models/VenmoVaultResponse.cs` |
| `VenmoWalletAdditionalAttributes` | Additional attributes associated with the use of this Venmo Wallet. | `Customer (customer): VenmoWalletCustomerInformation?`, `Vault (vault): VenmoWalletVaultAttributes?` | `Models/VenmoWalletAdditionalAttributes.cs` |
| `VenmoWalletAttributesResponse` | Additional attributes associated with the use of a Venmo Wallet. | `Vault (vault): VenmoVaultResponse?` | `Models/VenmoWalletAttributesResponse.cs` |
| `VenmoWalletCustomerInformation` | The details about a customer in PayPal's system of record. | `Id (id): string?`, `EmailAddress (email_address): string?`, `Phone (phone): PhoneWithType?`, `Name (name): Name?` | `Models/VenmoWalletCustomerInformation.cs` |
| `VenmoWalletExperienceContext` | Customizes the buyer experience during the approval process for payment with Venmo. Note: Partners and Marketplaces might configure shipping_preference during partner account setup, which overrides the request values. | `BrandName (brand_name): string?`, `ShippingPreference (shipping_preference): VenmoWalletExperienceContextShippingPreference? = VenmoWalletExperienceContextShippingPreference.GetFromFile`, `OrderUpdateCallbackConfig (order_update_callback_config): CallbackConfiguration?`, `UserAction (user_action): VenmoWalletExperienceContextUserAction? = VenmoWalletExperienceContextUserAction.Continue` | `Models/VenmoWalletExperienceContext.cs` |
| `VenmoWalletRequest` | Information needed to pay using Venmo. | `VaultId (vault_id): string?`, `EmailAddress (email_address): string?`, `ExperienceContext (experience_context): VenmoWalletExperienceContext?`, `Attributes (attributes): VenmoWalletAdditionalAttributes?` | `Models/VenmoWalletRequest.cs` |
| `VenmoWalletResponse` | Venmo wallet response. | `EmailAddress (email_address): string?`, `AccountId (account_id): string?`, `UserName (user_name): string?`, `Name (name): Name?`, `PhoneNumber (phone_number): PhoneNumber?`, `Address (address): Address?`, `ReturnFlow (return_flow): ReturnFlow? = ReturnFlow.Auto`, `Attributes (attributes): VenmoWalletAttributesResponse?` | `Models/VenmoWalletResponse.cs` |
| `VenmoWalletVaultAttributes` | Resource consolidating common request and response attirbutes for vaulting Venmo Wallet. | `StoreInVault (store_in_vault): StoreInVaultInstruction !req`, `Description (description): string?`, `UsagePattern (usage_pattern): VenmoPaymentTokenUsagePattern?`, `UsageType (usage_type): VenmoPaymentTokenUsageType !req`, `CustomerType (customer_type): VenmoPaymentTokenCustomerType? = VenmoPaymentTokenCustomerType.Consumer`, `PermitMultiplePaymentTokens (permit_multiple_payment_tokens): bool? = false` | `Models/VenmoWalletVaultAttributes.cs` |
