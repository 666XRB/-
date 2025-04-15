import datetime

class KnowledgeCard:
    def __init__(self, id, module, content, mnemonic, created_at, updated_at, query_count):
        self.id = id
        self.module = module
        self.content = content
        self.mnemonic = mnemonic
        self.created_at = created_at
        self.updated_at = updated_at
        self.query_count = query_count

    @staticmethod
    def create_new(module, content, mnemonic=None):
        now = datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        return KnowledgeCard(None, module, content, mnemonic, now, now, 0)

    def update(self, module, content, mnemonic=None):
        self.module = module
        self.content = content
        self.mnemonic = mnemonic
        # 只更新updated_at，不修改created_at
        self.updated_at = datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S")