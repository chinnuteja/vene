from typing import List, Dict, Any, Optional
from datetime import datetime

import numpy as np
from openfisca_core.simulation_builder import SimulationBuilder
from openfisca_japan import CountryTaxBenefitSystem
from .config import ATTRIBUTE_DICT, TAX_BENEFIT_DICT


def get_tax_benefit_info(tax_benefit_name: str) -> Dict[str, Any]:
    """
    指定された制度をcalc toolで計算するために必要なattributeのリストと出力単位、制度説明を返します。
    """
    if tax_benefit_name not in TAX_BENEFIT_DICT:
        return {}
    
    attributes = []
    benefit_info = TAX_BENEFIT_DICT[tax_benefit_name]
    for attr_entry in benefit_info.get("input_attribute", []):
        attr_name = attr_entry["name"]
        if attr_name in ATTRIBUTE_DICT:
            attr_info = ATTRIBUTE_DICT[attr_name].copy()
            attr_info["name"] = attr_name
            attr_info["required"] = attr_entry.get("required", False)
            attributes.append(attr_info)
    
    return {
        "input_attribute": attributes,
        "output_level": benefit_info.get("output_level", "member"),
        "description": benefit_info.get("description", "")
    }

def calc(household_list: List[Dict[str, Any]], output_tax_benefit_list: List[Dict[str, str]], date: Optional[str] = None) -> List[Dict[str, Any]]:
    """
    入力された世帯情報をもとに、入力で指定された制度の金額計算結果を出力します。
    """
    if date is None:
        date = datetime.now().strftime("%Y-%m-%d")
        
    tax_benefit_list = [tb for tb in output_tax_benefit_list if tb.get("name") in TAX_BENEFIT_DICT]
    
    if not tax_benefit_list:
        return household_list

    # OpenFisca-Japan の準備
    tax_benefit_system = CountryTaxBenefitSystem()
    
    # 予約済みのキー（特殊な処理が必要なもの）
    RESERVED_PERSON_KEYS = {"name", "年収", "person_id", "household_id", "person_role_in_household"}
    RESERVED_HH_KEYS = {"household_id"}

    # 全ての属性キーをスキャンして動的リストの受け皿を作成
    dynamic_person_keys = set()
    dynamic_hh_keys = set()
    for hh in household_list:
        hh_attr = hh.get("household_attribute", {}) or {}
        for k in hh_attr.keys():
            if k not in RESERVED_HH_KEYS:
                dynamic_hh_keys.add(k)
        
        for m in hh.get("member_attribute", []):
            for k in m.keys():
                if k not in RESERVED_PERSON_KEYS:
                    dynamic_person_keys.add(k)
    
    dynamic_person_data = {k: [] for k in dynamic_person_keys}
    dynamic_hh_data = {k: [] for k in dynamic_hh_keys}

    person_id_list = []
    household_id_list = []
    person_role_list = []
    income_list = []
    hh_id_list = []
    
    p_id = 0
    h_id = 0
    
    for hh in household_list:
        hh_id_list.append(h_id)
        hh_attr = hh.get("household_attribute", {}) or {}
        for k in dynamic_hh_keys:
            val = hh_attr.get(k)
            dynamic_hh_data[k].append(val if val is not None else "") # デフォルトは空文字

        members = hh.get("member_attribute", [])
        for m in members:
            if "name" not in m:
                m["name"] = f"member{p_id+1}"
            
            age = m.get("年齢", 0)
            # 18歳でも"子"のroleでないと児童手当対象にならないため20歳未満を"子"とする
            role = "子" if age < 20 else "親"  
            
            person_id_list.append(p_id)
            household_id_list.append(h_id)
            person_role_list.append(role)
            income_list.append(m.get("年収", 0))

            for k in dynamic_person_keys:
                val = m.get(k)
                # デフォルト値の判定: 数値っぽければ 0、そうでなければ空文字
                if val is None:
                    dynamic_person_data[k].append(0) 
                else:
                    dynamic_person_data[k].append(val)
            
            p_id += 1
        h_id += 1

    data_persons_dict = {
        "person_id": np.array(person_id_list, dtype=int),
        "household_id": np.array(household_id_list, dtype=int),
        "person_role_in_household": np.array(person_role_list, dtype=str),
        "収入": np.array(income_list, dtype=int),
    }
    for k, v in dynamic_person_data.items():
        # 型推論を行って ndarray を作成
        try:
            data_persons_dict[k] = np.array(v)
        except Exception:
            data_persons_dict[k] = np.array(v, dtype=str)

    data_households_dict = {
        "household_id": np.array(hh_id_list, dtype=int),
    }
    for k, v in dynamic_hh_data.items():
        try:
            data_households_dict[k] = np.array(v)
        except Exception:
            data_households_dict[k] = np.array(v, dtype=str)

    sb = SimulationBuilder()
    sb.create_entities(tax_benefit_system)

    sb.declare_person_entity("人物", data_persons_dict["person_id"])
    household_instance = sb.declare_entity("世帯", data_households_dict["household_id"])

    person_household = data_persons_dict["household_id"]
    person_household_role = data_persons_dict["person_role_in_household"]
    sb.join_with_persons(household_instance, person_household, person_household_role)

    simulation = sb.build(tax_benefit_system)

    # OpenFiscaの入力属性(variable)を設定
    # OpenFisca Python APIでは入力属性として元々の定義値("誕生年月日"等)だけでなく
    # 算出値("誕生年月日"から算出される"年齢"等)も直接設定できる
    for input_key, input_value in data_households_dict.items():
        if input_key == "household_id":
            continue
        try:
            simulation.set_input(input_key, date, input_value)
        except Exception:
            pass

    for input_key, input_value in data_persons_dict.items():
        if input_key in ["household_id", "person_role_in_household", "person_id"]:
            continue
        try:
            simulation.set_input(input_key, date, input_value)
        except Exception:
            pass

    for tb in tax_benefit_list:
        tax_benefit = tb.get("name")
        benefit_config = TAX_BENEFIT_DICT.get(tax_benefit, {})
        household_or_member = benefit_config.get("output_level", "member")
        try:
            amount_array = simulation.calculate(tax_benefit, date)
            if household_or_member == "member":
                # Person
                for p_id_val, amount in enumerate(amount_array):
                    hh_idx = household_id_list[p_id_val]
                    hh = household_list[hh_idx]
                    members = hh.get("member_attribute", [])
                    
                    local_idx = 0
                    for prev_hh_idx in range(hh_idx):
                        local_idx += len(household_list[prev_hh_idx].get("member_attribute", []))
                    member_local_idx = p_id_val - local_idx
                    
                    if member_local_idx < len(members):
                        m = members[member_local_idx]
                        if hasattr(np, "isnan"):
                            # Numpy version check for float parsing
                            try:
                                is_nan = np.isnan(amount)
                            except TypeError:
                                is_nan = False
                        else:
                            is_nan = False
                        
                        m[tax_benefit] = int(amount) if not is_nan else 0

            elif household_or_member == "household":
                # Household
                for h_id_val, amount in enumerate(amount_array):
                    hh = household_list[h_id_val]
                    if "household_attribute" not in hh or hh["household_attribute"] is None:
                        hh["household_attribute"] = {}
                        
                    try:
                        is_nan = np.isnan(amount)
                    except TypeError:
                        is_nan = False
                        
                    hh["household_attribute"][tax_benefit] = int(amount) if not is_nan else 0
        except Exception as e:
            # 万が一の計算エラーはスキップ
            print(f"[{tax_benefit}] Calculation skip. Error: {e}")
            pass

    return household_list

