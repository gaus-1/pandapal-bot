"""
Скрипт для создания и запуска JMeter тестов
Генерирует JMX файлы для нагрузочного тестирования
"""

import json
import xml.etree.ElementTree as ET
from pathlib import Path
from typing import Dict, List


def create_jmeter_test_plan(
    base_url: str,
    endpoints: List[Dict[str, str]],
    threads: int = 10,
    ramp_up: int = 10,
    duration: int = 60,
) -> str:
    """
    Создать JMeter test plan XML.

    Args:
        base_url: Базовый URL для тестирования
        endpoints: Список endpoints для тестирования
        threads: Количество потоков (пользователей)
        ramp_up: Время набора пользователей (секунды)
        duration: Длительность теста (секунды)

    Returns:
        str: XML содержимое test plan
    """
    # Создаём корневой элемент
    test_plan = ET.Element("jmeterTestPlan", version="1.2")
    hash_tree = ET.SubElement(test_plan, "hashTree")

    # TestPlan элемент
    test_plan_element = ET.SubElement(hash_tree, "TestPlan")
    test_plan_element.set("guiclass", "TestPlanGui")
    test_plan_element.set("testclass", "TestPlan")
    test_plan_element.set("testname", "PandaPal Load Test")
    test_plan_element.set("enabled", "true")
    ET.SubElement(test_plan_element, "stringProp", name="TestPlan.comments")
    ET.SubElement(test_plan_element, "boolProp", name="TestPlan.functional_mode").text = "false"
    ET.SubElement(test_plan_element, "boolProp", name="TestPlan.serialize_threadgroups").text = (
        "false"
    )
    ET.SubElement(test_plan_element, "stringProp", name="TestPlan.user_define_classpath")

    hash_tree_test_plan = ET.SubElement(hash_tree, "hashTree")

    # ThreadGroup
    thread_group = ET.SubElement(hash_tree_test_plan, "ThreadGroup")
    thread_group.set("guiclass", "ThreadGroupGui")
    thread_group.set("testclass", "ThreadGroup")
    thread_group.set("testname", "User Thread Group")
    thread_group.set("enabled", "true")
    ET.SubElement(thread_group, "stringProp", name="ThreadGroup.on_sample_error").text = "continue"
    ET.SubElement(
        thread_group,
        "elementProp",
        name="ThreadGroup.main_controller",
        elementType="LoopController",
        guiclass="LoopControllerGui",
        testclass="LoopController",
        testname="Loop Controller",
        enabled="true",
    )
    ET.SubElement(thread_group, "stringProp", name="ThreadGroup.num_threads").text = str(threads)
    ET.SubElement(thread_group, "stringProp", name="ThreadGroup.ramp_time").text = str(ramp_up)
    ET.SubElement(thread_group, "boolProp", name="ThreadGroup.scheduler").text = "true"
    ET.SubElement(thread_group, "stringProp", name="ThreadGroup.duration").text = str(duration)
    ET.SubElement(thread_group, "stringProp", name="ThreadGroup.delay")

    hash_tree_thread_group = ET.SubElement(hash_tree_test_plan, "hashTree")

    # HTTP Request Defaults
    http_defaults = ET.SubElement(hash_tree_thread_group, "ConfigTestElement")
    http_defaults.set("guiclass", "HttpDefaultsGui")
    http_defaults.set("testclass", "ConfigTestElement")
    http_defaults.set("testname", "HTTP Request Defaults")
    http_defaults.set("enabled", "true")
    ET.SubElement(http_defaults, "stringProp", name="HTTPSampler.domain").text = (
        base_url.replace("https://", "").replace("http://", "").split("/")[0]
    )
    ET.SubElement(http_defaults, "stringProp", name="HTTPSampler.protocol").text = (
        "https" if base_url.startswith("https") else "http"
    )
    ET.SubElement(http_defaults, "stringProp", name="HTTPSampler.port")
    ET.SubElement(http_defaults, "stringProp", name="HTTPSampler.path")

    hash_tree_http_defaults = ET.SubElement(hash_tree_thread_group, "hashTree")

    # Добавляем HTTP запросы для каждого endpoint
    for endpoint in endpoints:
        http_request = ET.SubElement(hash_tree_http_defaults, "HTTPSamplerProxy")
        http_request.set("guiclass", "HttpTestSampleGui")
        http_request.set("testclass", "HTTPSamplerProxy")
        http_request.set("testname", endpoint.get("name", endpoint["path"]))
        http_request.set("enabled", "true")
        ET.SubElement(
            http_request,
            "elementProp",
            name="HTTPsampler.Arguments",
            elementType="Arguments",
            guiclass="HTTPArgumentsPanel",
            testclass="Arguments",
            testname="User Defined Variables",
            enabled="true",
        )
        ET.SubElement(http_request, "stringProp", name="HTTPSampler.path").text = endpoint["path"]
        ET.SubElement(http_request, "stringProp", name="HTTPSampler.method").text = endpoint.get(
            "method", "GET"
        )

        hash_tree_http_request = ET.SubElement(hash_tree_http_defaults, "hashTree")
        ET.SubElement(hash_tree_http_request, "hashTree")

    # Конвертируем в строку
    ET.indent(test_plan)
    return ET.tostring(test_plan, encoding="unicode", xml_declaration=True)


def generate_jmeter_script(output_file: str = "jmeter_test_plan.jmx"):
    """Генерация JMeter test plan для PandaPal"""
    base_url = "https://pandapal.ru"
    endpoints = [
        {"name": "Health Check", "path": "/health", "method": "GET"},
        {"name": "Get User", "path": "/api/miniapp/user/123456789", "method": "GET"},
    ]

    test_plan_xml = create_jmeter_test_plan(
        base_url=base_url,
        endpoints=endpoints,
        threads=10,
        ramp_up=10,
        duration=60,
    )

    with open(output_file, "w", encoding="utf-8") as f:
        f.write(test_plan_xml)

    print(f"✅ JMeter test plan создан: {output_file}")
    print(f"📋 Endpoints: {len(endpoints)}")
    print(f"👥 Threads: 10")
    print(f"⏱️ Duration: 60s")
    print(f"\nЗапуск:")
    print(f"  jmeter -n -t {output_file} -l results.jtl")


if __name__ == "__main__":
    generate_jmeter_script()
