# Sample Data

Synthetic, generic PRDs you can use to test and demo the orchestrator. They
contain no real or proprietary information.

| File | Format | Feature |
|------|--------|---------|
| `prd_user_authentication.md` | Markdown (free-text) | User auth & account management |
| `prd_shopping_cart.json` | JSON (PRD schema) | Shopping cart & checkout |

## How the ingester reads these

- **Markdown / `.txt`** — the title is taken from the first `# Heading`, and each
  bullet (`- ` / `* `) or numbered line becomes a requirement.
- **JSON** — must match the `PRD` schema keys: `prd_id`, `title`, `description`,
  and `requirements` (a list of `{id, description, priority}` objects).

## Run the pipeline with sample data

Make sure Ollama is running with the model pulled (`ollama pull mistral`), then:

```bash
# Markdown PRD
python app/main.py \
  --prd-file sample_data/prd_user_authentication.md \
  --prd-title "User Authentication" \
  --feature-title "Email + password sign-in with 2FA" \
  --platform CLOUD

# JSON PRD
python app/main.py \
  --prd-file sample_data/prd_shopping_cart.json \
  --feature-title "Cart and checkout flow" \
  --platform CORE
```

Add your own PRDs here in the same format to test different features.
