##

# `ktg_chat_django` Installation & Usage

## Installation

To install or upgrade the latest version:

```bash
pip install git+https://github.com/KayakTech/ktg_chat_django.git
```

### Specific Branch Installation

To install from a specific branch:

```bash
pip install git+https://github.com/KayakTech/ktg_chat_django.git@branch_name

```

# To Uninstall

```bash
pip uninstall ktg_chat_django
```

## Usage

```python
from ktg_storage.models import Storage



# THIS SEEETING MUST BE IN THE settings.py file

CHAT_API_BASE_URL = "http://localhost"

CHAT_ORGANISATION_TOKEN = 'your_organisation_token_here'

# Serializer mapping for object types
OBJECT_TYPE_SERIALIZERS = {
    # Format:
    # 1. Model name =Repairs
    # 2. Key for the serializer = serializer
    # 3. Path to the serializer (e.g., "app_name.serializers.SerializerName")
    "Repairs": {
        "serializer": "repairs.serializers.RepairSerializer",
    },
}

CHAT_MODELS = OBJECT_TYPE_SERIALIZERS.keys()



```

---
