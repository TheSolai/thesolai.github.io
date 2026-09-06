# Store

This directory is owned by the `sol-merchant` agent. The agent:

- Creates product pages at `store/<slug>/index.md`
- Drops structured metadata at `store/<slug>/_meta.json`
- Generates cover images at `store/<slug>/cover.png` (1200×630)
- Appends to the catalog at `_data/store.json`
- Updates `store/index.html` (the catalog page itself is hand-maintained, the agent only appends to `<!-- PRODUCTS_START -->` ... `<!-- PRODUCTS_END -->`)

The catalog page (`store/index.html`) is human-maintained. Edit the header, the empty-state copy, and the layout as you like. The agent will only touch the `<!-- PRODUCTS_START -->` block.

## Adding a product manually

If you want to publish something without going through the agent:

1. Create `store/<slug>/` with `index.md`, `_meta.json`, `cover.png`
2. Append the entry to `_data/store.json`
3. Commit and push

The catalog page will pick it up automatically.

## Removing a product

1. Delete `store/<slug>/`
2. Remove the entry from `_data/store.json`
3. If it's live on Gumroad / itch.io, unpublish or delete the listing there too
4. Commit and push
