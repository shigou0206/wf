import unittest
import ast
from typing import Dict, Any, List
from graph.models.expression import (
    get_safe_environment,
    WorkflowDataProxy,
    split_template,
    ASTHook,
    parse_and_transform,
    get_safe_globals,
    execute_expression,
    Expression,
    evaluate_template
)


class TestExpression(unittest.TestCase):
    def setUp(self):
        # 设置测试数据
        self.test_data = {
            "user": {
                "name": "Test User",
                "email": "test@example.com",
                "age": 30
            },
            "items": [1, 2, 3, 4, 5],
            "settings": {
                "theme": "dark",
                "notifications": True
            }
        }
        
        # 创建表达式计算器
        self.expression = Expression(self.test_data)

    def test_get_safe_environment(self):
        """测试安全 Jinja2 环境创建"""
        env = get_safe_environment()
        self.assertIsNotNone(env)
        
        # 测试自定义分隔符
        self.assertEqual(env.variable_start_string, '{{')
        self.assertEqual(env.variable_end_string, '}}')
        
        # 测试简单模板渲染
        template = env.from_string("Hello, {{ user.name }}!")
        result = template.render(user={"name": "John"})
        self.assertEqual(result, "Hello, John!")
        
        # 测试带有特殊字符的变量
        template = env.from_string("Value: {{ data_with_special_chars.value }}")
        result = template.render(data_with_special_chars={"value": 42})
        self.assertEqual(result, "Value: 42")

    def test_workflow_data_proxy(self):
        """测试工作流数据代理"""
        proxy = WorkflowDataProxy(self.test_data)
        data_proxy = proxy.get_data_proxy()
        
        # 检查数据是否正确传递
        self.assertEqual(data_proxy["data"], self.test_data)
        
        # 检查是否包含安全函数
        self.assertIn("len", data_proxy)
        self.assertIn("min", data_proxy)
        self.assertIn("max", data_proxy)
        self.assertIn("sum", data_proxy)
        
        # 测试函数可用性
        self.assertEqual(data_proxy["len"]([1, 2, 3]), 3)
        self.assertEqual(data_proxy["sum"]([1, 2, 3]), 6)

    def test_split_template(self):
        """测试模板拆分功能"""
        # 测试简单模板
        template = "Hello, {{ name }}!"
        parts = split_template(template)
        self.assertEqual(len(parts), 3)
        self.assertEqual(parts[0], {"type": "text", "value": "Hello, "})
        self.assertEqual(parts[1], {"type": "code", "value": "name"})
        self.assertEqual(parts[2], {"type": "text", "value": "!"})
        
        # 测试多个表达式
        template = "{{ greeting }}, {{ name }}! Your score is {{ score }}."
        parts = split_template(template)
        self.assertEqual(len(parts), 6)
        self.assertEqual(parts[0], {"type": "code", "value": "greeting"})
        self.assertEqual(parts[1], {"type": "text", "value": ", "})
        self.assertEqual(parts[2], {"type": "code", "value": "name"})
        self.assertEqual(parts[3], {"type": "text", "value": "! Your score is "})
        self.assertEqual(parts[4], {"type": "code", "value": "score"})
        
        # 测试无表达式模板
        template = "Hello, world!"
        parts = split_template(template)
        self.assertEqual(len(parts), 1)
        self.assertEqual(parts[0], {"type": "text", "value": "Hello, world!"})

    def test_ast_hook(self):
        """测试 AST 钩子功能"""
        # 创建一个自定义 AST 钩子，将所有字符串常量转为大写
        class UppercaseStringHook(ASTHook):
            def after(self, node: ast.AST) -> ast.AST:
                if isinstance(node, ast.Constant) and isinstance(node.value, str):
                    node.value = node.value.upper()
                return node
        
        # 测试钩子应用
        hooks = [UppercaseStringHook()]
        expr_ast = parse_and_transform("'hello' + ' world'", hooks)
        
        # 编译并执行转换后的 AST
        code = compile(expr_ast, filename="<ast>", mode="eval")
        result = eval(code)
        
        self.assertEqual(result, "HELLO WORLD")

    def test_parse_and_transform(self):
        """测试表达式解析和转换"""
        # 测试简单表达式
        expr_ast = parse_and_transform("1 + 2", [])
        self.assertIsInstance(expr_ast, ast.Expression)
        
        # 测试复杂表达式
        expr_ast = parse_and_transform("len([1, 2, 3]) * 2", [])
        self.assertIsInstance(expr_ast, ast.Expression)
        
        # 测试语法错误处理
        with self.assertRaises(SyntaxError):
            parse_and_transform("1 +", [])

    def test_get_safe_globals(self):
        """测试安全全局环境创建"""
        # 测试默认安全全局环境
        safe_globals = get_safe_globals()
        self.assertIn("__builtins__", safe_globals)
        builtins = safe_globals["__builtins__"]
        
        # 检查安全函数是否存在
        self.assertIn("len", builtins)
        self.assertIn("min", builtins)
        self.assertIn("max", builtins)
        
        # 检查危险函数是否被排除
        self.assertNotIn("eval", builtins)
        self.assertNotIn("exec", builtins)
        self.assertNotIn("__import__", builtins)
        
        # 测试自定义全局环境
        custom_globals = {"custom_var": 42}
        safe_globals = get_safe_globals(custom_globals)
        self.assertEqual(safe_globals["custom_var"], 42)

    def test_execute_expression(self):
        """测试表达式执行功能"""
        # 测试简单表达式
        result = execute_expression("1 + 2", {})
        self.assertEqual(result, 3)
        
        # 测试带上下文的表达式
        context = {"x": 10, "y": 5}
        result = execute_expression("x * y", context)
        self.assertEqual(result, 50)
        
        # 测试内置函数
        result = execute_expression("len([1, 2, 3])", {})
        self.assertEqual(result, 3)
        
        # 测试错误处理
        result = execute_expression("1 / 0", {})
        self.assertTrue(isinstance(result, str))
        self.assertTrue(result.startswith("[Error:"))

    def test_expression_class(self):
        """测试 Expression 类功能"""
        # 测试非表达式字符串
        result = self.expression.resolve_expression("Hello, world!")
        self.assertEqual(result, "Hello, world!")
        
        # 测试简单表达式
        result = self.expression.resolve_expression("=1 + 2")
        self.assertEqual(result, 3)
        
        # 测试访问数据
        result = self.expression.resolve_expression("=data['user']['name']")
        self.assertEqual(result, "Test User")
        
        # 测试使用内置函数
        result = self.expression.resolve_expression("=len(data['items'])")
        self.assertEqual(result, 5)
        
        # 测试复杂表达式
        result = self.expression.resolve_expression("=data['user']['age'] * 2")
        self.assertEqual(result, 60)

    def test_evaluate_template(self):
        """测试模板表达式计算"""
        # 测试简单模板
        template = "Hello, {{ data['user']['name'] }}!"
        result = evaluate_template(template, {"data": self.test_data})
        self.assertEqual(result, "Hello, Test User!")
        
        # 测试多个表达式
        template = "{{ data['user']['name'] }} is {{ data['user']['age'] }} years old."
        result = evaluate_template(template, {"data": self.test_data})
        self.assertEqual(result, "Test User is 30 years old.")
        
        # 测试使用内置函数
        template = "Items count: {{ len(data['items']) }}"
        result = evaluate_template(template, {"data": self.test_data})
        self.assertEqual(result, "Items count: 5")
        
        # 测试错误处理
        template = "Result: {{ 1 / 0 }}"
        result = evaluate_template(template, {})
        self.assertTrue("Error" in result)
        
        # 测试自定义 AST 钩子
        class DoubleNumberHook(ASTHook):
            def after(self, node: ast.AST) -> ast.AST:
                if isinstance(node, ast.Constant) and isinstance(node.value, (int, float)):
                    node.value = node.value * 2
                return node
        
        template = "Double: {{ 5 }}"
        result = evaluate_template(template, {}, hooks=[DoubleNumberHook()])
        self.assertEqual(result, "Double: 10")

    def test_complex_scenarios(self):
        """测试复杂场景"""
        # 测试嵌套数据访问和函数调用
        template = """
        User: {{ data['user']['name'] }}
        Items: {{ len(data['items']) }}
        First item: {{ data['items'][0] }}
        Last item: {{ data['items'][-1] }}
        Sum of items: {{ sum(data['items']) }}
        Theme: {{ data['settings']['theme'].upper() }}
        """
        result = evaluate_template(template, {"data": self.test_data})
        self.assertIn("User: Test User", result)
        self.assertIn("Items: 5", result)
        self.assertIn("First item: 1", result)
        self.assertIn("Last item: 5", result)
        self.assertIn("Sum of items: 15", result)
        self.assertIn("Theme: DARK", result)
        
        # 测试条件表达式
        template = "Status: {{ 'Adult' if data['user']['age'] >= 18 else 'Minor' }}"
        result = evaluate_template(template, {"data": self.test_data})
        self.assertEqual(result, "Status: Adult")
        
        # 测试列表推导
        template = "Doubled items: {{ [item * 2 for item in data['items']] }}"
        result = evaluate_template(template, {"data": self.test_data})
        self.assertEqual(result, "Doubled items: [2, 4, 6, 8, 10]")


if __name__ == "__main__":
    unittest.main() 