class Field:
    def __init__(self, name, label, field_type="text", required=False, min_length=None, max_length=None):
        self.name = name
        self.label = label
        self.type = field_type
        self.required = required
        self.min_length = min_length
        self.max_length = max_length
        self.value = ""
        self.error = None