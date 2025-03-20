import unittest
from typing import Dict, Any, List
from graph.models.utils import (
    get_parameter_dependencies,
    get_parameter_resolve_order,
    get_node_parameters
)
from graph.models.node_model import NodeProperties


class TestGraphModelUtils(unittest.TestCase):
    def setUp(self):
        # 创建测试用的节点属性
        self.simple_node_properties = [
            NodeProperties(
                name="param1",
                display_name="Parameter 1",
                type="string",
                default="default1",
                display_options={}
            ),
            NodeProperties(
                name="param2",
                display_name="Parameter 2",
                type="number",
                default=0,
                display_options={}
            )
        ]
        
        # 创建带有依赖关系的节点属性
        self.dependent_node_properties = [
            NodeProperties(
                name="param1",
                display_name="Parameter 1",
                type="string",
                default="default1",
                display_options={}
            ),
            NodeProperties(
                name="param2",
                display_name="Parameter 2",
                type="number",
                default=0,
                display_options={"show": {"param1": "value1"}}
            ),
            NodeProperties(
                name="param3",
                display_name="Parameter 3",
                type="boolean",
                default=False,
                display_options={"show": {"param2": 1}}
            )
        ]
        
        # 创建带有集合类型的节点属性
        self.collection_node_properties = [
            NodeProperties(
                name="param1",
                display_name="Parameter 1",
                type="string",
                default="default1",
                display_options={}
            ),
            NodeProperties(
                name="collection1",
                display_name="Collection 1",
                type="collection",
                default={},
                type_options={"multipleValues": False},
                options=[
                    NodeProperties(
                        name="subParam1",
                        display_name="Sub Parameter 1",
                        type="string",
                        default="subDefault1",
                        display_options={}
                    )
                ],
                display_options={}
            ),
            NodeProperties(
                name="collection2",
                display_name="Collection 2",
                type="collection",
                default=[],
                type_options={"multipleValues": True},
                options=[
                    NodeProperties(
                        name="subParam2",
                        display_name="Sub Parameter 2",
                        type="number",
                        default=0,
                        display_options={}
                    )
                ],
                display_options={}
            )
        ]
        
        # 创建带有固定集合类型的节点属性
        self.fixed_collection_node_properties = [
            NodeProperties(
                name="param1",
                display_name="Parameter 1",
                type="string",
                default="default1",
                display_options={}
            ),
            NodeProperties(
                name="fixedCollection1",
                display_name="Fixed Collection 1",
                type="fixedCollection",
                default={},
                options=[
                    NodeProperties(
                        name="subParam1",
                        display_name="Sub Parameter 1",
                        type="string",
                        default="subDefault1",
                        display_options={}
                    )
                ],
                display_options={}
            )
        ]

    def test_get_parameter_dependencies(self):
        # 测试无依赖关系的情况
        dependencies = get_parameter_dependencies(self.simple_node_properties)
        self.assertEqual(dependencies, {"param1": [], "param2": []})
        
        # 测试有依赖关系的情况
        dependencies = get_parameter_dependencies(self.dependent_node_properties)
        self.assertEqual(dependencies, {
            "param1": [],
            "param2": ["param1"],
            "param3": ["param2"]
        })

    def test_get_parameter_resolve_order(self):
        # 测试无依赖关系的情况
        dependencies = get_parameter_dependencies(self.simple_node_properties)
        order = get_parameter_resolve_order(self.simple_node_properties, dependencies)
        # 无依赖关系时，顺序可以是任意的
        self.assertEqual(set(order), {0, 1})
        
        # 测试有依赖关系的情况
        dependencies = get_parameter_dependencies(self.dependent_node_properties)
        order = get_parameter_resolve_order(self.dependent_node_properties, dependencies)
        # 有依赖关系时，顺序应该是确定的
        self.assertEqual(order, [0, 1, 2])  # param1 -> param2 -> param3

    def test_get_node_parameters_simple(self):
        # 测试简单参数
        node_values = {"param1": "value1", "param2": 42}
        
        # 测试返回默认值
        params = get_node_parameters(
            self.simple_node_properties,
            node_values,
            return_defaults=True,
            return_none_displayed=False,
            node=None
        )
        self.assertEqual(params, {"param1": "value1", "param2": 42})
        
        # 测试不返回默认值
        params = get_node_parameters(
            self.simple_node_properties,
            node_values,
            return_defaults=False,
            return_none_displayed=False,
            node=None
        )
        self.assertEqual(params, {"param1": "value1", "param2": 42})
        
        # 测试值等于默认值时不返回
        node_values = {"param1": "default1", "param2": 42}
        params = get_node_parameters(
            self.simple_node_properties,
            node_values,
            return_defaults=False,
            return_none_displayed=False,
            node=None
        )
        self.assertEqual(params, {"param2": 42})

    def test_get_node_parameters_collection(self):
        # 测试集合类型参数
        node_values = {
            "param1": "value1",
            "collection1": {"subParam1": "subValue1"},
            "collection2": [{"subParam2": 1}, {"subParam2": 2}]
        }
        
        params = get_node_parameters(
            self.collection_node_properties,
            node_values,
            return_defaults=True,
            return_none_displayed=False,
            node=None
        )
        
        self.assertEqual(params["param1"], "value1")
        self.assertEqual(params["collection1"], {"subParam1": "subValue1"})
        self.assertEqual(params["collection2"], [{"subParam2": 1}, {"subParam2": 2}])

    def test_get_node_parameters_fixed_collection(self):
        # 测试固定集合类型参数
        node_values = {
            "param1": "value1",
            "fixedCollection1": {
                "values": [
                    {"subParam1": "subValue1"},
                    {"subParam1": "subValue2"}
                ]
            }
        }
        
        params = get_node_parameters(
            self.fixed_collection_node_properties,
            node_values,
            return_defaults=True,
            return_none_displayed=False,
            node=None
        )
        
        self.assertEqual(params["param1"], "value1")
        self.assertEqual(
            params["fixedCollection1"]["values"],
            [{"subParam1": "subValue1"}, {"subParam1": "subValue2"}]
        )

    def test_get_node_parameters_only_simple_types(self):
        # 测试只返回简单类型
        node_values = {
            "param1": "value1",
            "collection1": {"subParam1": "subValue1"},
            "collection2": [{"subParam2": 1}, {"subParam2": 2}]
        }
        
        params = get_node_parameters(
            self.collection_node_properties,
            node_values,
            return_defaults=True,
            return_none_displayed=False,
            node=None,
            only_simple_types=True
        )
        
        self.assertEqual(params, {"param1": "value1"})

    def test_duplicate_parameter_names(self):
        # 测试重复参数名
        duplicate_node_properties = [
            NodeProperties(
                name="param1",
                display_name="Parameter 1",
                type="string",
                default="default1",
                display_options={}
            ),
            NodeProperties(
                name="param1",
                display_name="Parameter 1 Duplicate",
                type="number",
                default=0,
                display_options={}
            )
        ]
        
        node_values = {"param1": "value1"}
        
        params = get_node_parameters(
            duplicate_node_properties,
            node_values,
            return_defaults=True,
            return_none_displayed=False,
            node=None
        )
        
        # 重复参数名应该被忽略
        self.assertEqual(params, {})


if __name__ == "__main__":
    unittest.main() 