# DS-001: 数据源管理

## 用户故事

作为系统管理员，我希望能够管理系统的数据源配置，包括添加、编辑、删除数据源，配置 API Token，测试数据源连接，以便系统能够从不同的数据源采集股票数据。

## 验收标准

### 功能需求

#### AC1: 查看数据源列表
**Given**: 管理员登录管理端
**When**: 进入数据源管理页面
**Then**: 显示所有数据源的列表
**And**: 包含名称、类型、API地址、状态、最后测试时间等信息

#### AC2: 新增数据源
**Given**: 在数据源管理页面
**When**: 点击新增数据源按钮
**Then**: 显示新增数据源表单
**And**: 包含名称、类型、API地址、Token、描述等字段

#### AC3: 编辑数据源
**Given**: 在数据源列表
**When**: 点击某个数据源的编辑按钮
**Then**: 显示编辑数据源表单
**And**: Token 字段为掩码显示（不显示明文）

#### AC4: 删除数据源
**Given**: 在数据源列表
**When**: 点击某个数据源的删除按钮
**Then**: 显示确认对话框
**And**: 确认后删除数据源
**And**: 如果该数据源有关联的同步任务，禁止删除

#### AC5: 测试数据源连接
**Given**: 在数据源列表或编辑页面
**When**: 点击测试连接按钮
**Then**: 系统尝试连接数据源
**And**: 返回连接结果（成功/失败及详细信息）
**And**: 记录最后测试时间和测试结果

#### AC6: 启用/禁用数据源
**Given**: 在数据源列表
**When**: 切换数据源的状态开关
**Then**: 数据源状态更新
**And**: 禁用的数据源不会被调度执行

#### AC7: Token 配置
**Given**: 新增或编辑数据源
**When**: 填写 Token 字段
**Then**: Token 通过配置文件加密存储
**And**: 列表和详情接口不返回完整 Token

### 安全需求

#### SC1: Token 安全存储
- Token 加密存储在数据库
- API 响应中 Token 脱敏（只显示前后几位）
- 支持通过配置文件配置 Token

#### SC2: 操作权限
- 仅管理员可管理数据源
- 所有操作记录操作日志

## 表单字段要求

### 新增/编辑数据源表单

| 字段 | 类型 | 必填 | 验证规则 |
|------|------|------|----------|
| 数据源名称 | 文本 | 是 | 2-50字符，唯一 |
| 数据源类型 | 选择 | 是 | Tushare/AKShare/自定义 |
| API地址 | 文本 | 是 | 合法 URL |
| Token | 密码 | 否 | 数据源需要时必填 |
| 描述 | 文本 | 否 | 最多200字符 |
| 状态 | 开关 | 是 | 启用/禁用，默认启用 |

## 技术实现

### 数据库模型

```sql
-- 数据源配置表
CREATE TABLE data_sources (
    id INT PRIMARY KEY AUTO_INCREMENT,
    name VARCHAR(50) UNIQUE NOT NULL COMMENT '数据源名称',
    source_type VARCHAR(20) NOT NULL COMMENT '类型:tushare,akshare,custom',
    api_url VARCHAR(255) NOT NULL COMMENT 'API地址',
    token_encrypted VARCHAR(500) COMMENT '加密后的Token',
    description VARCHAR(200) COMMENT '描述',
    status TINYINT DEFAULT 1 COMMENT '状态:1启用 0禁用',
    last_test_at DATETIME COMMENT '最后测试时间',
    last_test_result TINYINT COMMENT '最后测试结果:1成功 0失败',
    last_test_message VARCHAR(500) COMMENT '最后测试信息',
    created_at DATETIME DEFAULT CURRENT_TIMESTAMP,
    updated_at DATETIME DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP
);
```

### Pydantic 模型

```python
class DataSourceBase(BaseModel):
    name: str = Field(..., min_length=2, max_length=50)
    source_type: str = Field(..., pattern='^(tushare|akshare|custom)$')
    api_url: str = Field(..., max_length=255)
    token: Optional[str] = Field(None, max_length=500)
    description: Optional[str] = Field(None, max_length=200)
    status: int = Field(1, ge=0, le=1)

class DataSourceCreate(DataSourceBase):
    pass

class DataSourceUpdate(BaseModel):
    name: Optional[str] = Field(None, min_length=2, max_length=50)
    source_type: Optional[str] = None
    api_url: Optional[str] = None
    token: Optional[str] = None  # 为空表示不修改
    description: Optional[str] = None
    status: Optional[int] = None

class DataSourceResponse(BaseModel):
    id: int
    name: str
    source_type: str
    api_url: str
    token_masked: str  # 脱敏后的Token
    description: Optional[str]
    status: int
    last_test_at: Optional[datetime]
    last_test_result: Optional[int]
    last_test_message: Optional[str]
    created_at: datetime
```

### 数据源适配器设计

```python
# 数据源适配器抽象基类
class DataSourceAdapter(ABC):
    """数据源适配器接口"""

    @abstractmethod
    async def test_connection(self, token: str) -> dict:
        """测试连接"""
        pass

    @abstractmethod
    async def fetch_data(self, interface: str, params: dict, token: str) -> list:
        """获取数据"""
        pass

# Tushare 适配器
class TushareAdapter(DataSourceAdapter):
    async def test_connection(self, token: str) -> dict:
        # 调用 Tushare 简单接口验证 Token
        pass

# 适配器工厂
class DataSourceAdapterFactory:
    @staticmethod
    def get_adapter(source_type: str) -> DataSourceAdapter:
        adapters = {
            'tushare': TushareAdapter,
            'akshare': AKShareAdapter,
        }
        return adapters.get(source_type, CustomAdapter)()
```

### Token 加密工具

```python
from cryptography.fernet import Fernet

def encrypt_token(token: str) -> str:
    """加密 Token"""
    f = Fernet(get_encryption_key())
    return f.encrypt(token.encode()).decode()

def decrypt_token(encrypted: str) -> str:
    """解密 Token"""
    f = Fernet(get_encryption_key())
    return f.decrypt(encrypted.encode()).decode()

def mask_token(token: str) -> str:
    """Token 脱敏"""
    if not token or len(token) <= 8:
        return '****'
    return f"{token[:4]}****{token[-4:]}"
```

## API 接口

### GET /api/v1/admin/data-sources
获取数据源列表

**请求参数**:
- `page`: 页码，默认 1
- `page_size`: 每页数量，默认 10
- `search`: 搜索关键词（名称）
- `status`: 状态筛选

**响应示例**:
```json
{
  "code": 0,
  "data": {
    "list": [
      {
        "id": 1,
        "name": "Tushare主数据源",
        "source_type": "tushare",
        "api_url": "http://api.tushare.pro",
        "token_masked": "0289****3a6f",
        "description": "Tushare Pro 接口",
        "status": 1,
        "last_test_at": "2026-08-08T10:00:00",
        "last_test_result": 1,
        "last_test_message": "连接成功"
      }
    ],
    "page": 1,
    "page_size": 10,
    "total": 1
  }
}
```

### POST /api/v1/admin/data-sources
创建数据源

**请求参数**:
```json
{
  "name": "Tushare主数据源",
  "source_type": "tushare",
  "api_url": "http://api.tushare.pro",
  "token": "your-tushare-token",
  "description": "Tushare Pro 接口",
  "status": 1
}
```

### PUT /api/v1/admin/data-sources/{source_id}
更新数据源

### DELETE /api/v1/admin/data-sources/{source_id}
删除数据源（有关联同步任务时拒绝删除）

### POST /api/v1/admin/data-sources/{source_id}/test
测试数据源连接

**响应示例**:
```json
{
  "code": 0,
  "message": "连接成功",
  "data": {
    "success": true,
    "message": "Token 验证成功",
    "response_time": 350
  }
}
```

## 测试用例

### 正常流程
1. 新增一个 Tushare 数据源，填写正确的 Token
2. 点击测试连接，验证返回成功
3. 验证数据库中 Token 已加密存储
4. 编辑数据源，验证 Token 脱敏显示
5. 列表中查看数据源信息

### 边界情况
1. 测试连接时 Token 错误，验证返回失败信息
2. 删除有关联同步任务的数据源，验证被拒绝
3. 禁用数据源，验证不会被调度执行

## 相关文档

- Feature Map: feature-map.md
- 下一个 Story: ds-002-sync-task-management.md