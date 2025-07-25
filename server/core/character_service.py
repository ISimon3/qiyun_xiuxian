# 角色相关业务逻辑服务

from typing import Optional
from sqlalchemy.ext.asyncio import AsyncSession

from server.database.models import Character
from shared.schemas import (
    CharacterInfo, CharacterAttributes, CharacterTrainingAttributes,
    EquipmentAttributes, EquipmentSet, EquippedItem, EquipmentInfo
)
from shared.utils import calculate_base_attributes, calculate_final_attributes
from shared.constants import CULTIVATION_REALMS


class CharacterService:
    """角色业务逻辑服务"""
    
    @staticmethod
    def build_character_info(character: Character, include_equipment: bool = False) -> CharacterInfo:
        """
        从数据库模型构建角色信息响应模型
        计算角色的完整属性信息
        """
        # 计算基础属性（基于境界）
        base_attributes = calculate_base_attributes(character.cultivation_realm)

        # 构建修习属性
        training_attributes = CharacterTrainingAttributes(
            hp_training=character.hp_training,
            physical_attack_training=character.physical_attack_training,
            magic_attack_training=character.magic_attack_training,
            physical_defense_training=character.physical_defense_training,
            magic_defense_training=character.magic_defense_training
        )

        # 计算装备属性加成
        equipment_bonuses = []
        equipment_set = None

        if character.equipped_items:
            # 构建装备信息
            equipped_items = {}

            for equipped_item in character.equipped_items:
                # 构建装备属性
                if equipped_item.actual_attributes:
                    equipment_attrs = EquipmentAttributes(**equipped_item.actual_attributes)
                    equipment_bonuses.append(equipment_attrs)

                # 构建装备信息（如果需要详细信息）
                if include_equipment and equipped_item.item:
                    equipment_info = EquipmentInfo(
                        id=equipped_item.item.id,
                        name=equipped_item.item.name,
                        description=equipped_item.item.description or "",
                        equipment_slot=equipped_item.slot,
                        quality=equipped_item.item.quality,
                        required_realm=equipped_item.item.required_realm or 0,
                        attributes=equipment_attrs,
                        attribute_variation=equipped_item.attribute_variation,
                        special_effects=equipped_item.item.special_effects.get("effects", []) if equipped_item.item.special_effects else None
                    )

                    equipped_item_info = EquippedItem(
                        slot=equipped_item.slot,
                        equipment_id=equipped_item.item.id,
                        equipment_info=equipment_info
                    )

                    equipped_items[equipped_item.slot.lower()] = equipped_item_info

            # 构建装备套装信息
            if include_equipment:
                equipment_set = EquipmentSet(
                    weapon=equipped_items.get("weapon"),
                    armor=equipped_items.get("armor"),
                    helmet=equipped_items.get("helmet"),
                    boots=equipped_items.get("boots"),
                    bracelet=equipped_items.get("bracelet"),
                    magic_weapon=equipped_items.get("magic_weapon")
                )

        # 计算最终属性（基础属性 + 修习属性 + 装备属性）
        final_attributes = calculate_final_attributes(
            base_attributes,
            training_attributes,
            equipment_bonuses
        )

        # 构建角色信息
        character_info = CharacterInfo(
            id=character.id,
            name=character.name,
            cultivation_exp=character.cultivation_exp,
            cultivation_realm=character.cultivation_realm,
            spiritual_root=character.spiritual_root,
            luck_value=character.luck_value,
            gold=character.gold,
            spirit_stone=character.spirit_stone,
            created_at=character.created_at,
            last_active=character.last_active,
            cultivation_focus=character.cultivation_focus,
            attributes=final_attributes,
            training_attributes=training_attributes,
            equipment=equipment_set
        )

        return character_info
    
    @staticmethod
    def get_realm_name(realm_level: int) -> str:
        """获取境界名称"""
        if 0 <= realm_level < len(CULTIVATION_REALMS):
            return CULTIVATION_REALMS[realm_level]
        return "未知境界"
    
    @staticmethod
    def calculate_breakthrough_success_rate(
        character: Character,
        target_realm: int,
        use_items: Optional[list] = None
    ) -> float:
        """计算突破成功率"""
        from shared.constants import BREAKTHROUGH_CONFIG

        # 基础成功率
        base_rate = BREAKTHROUGH_CONFIG.get("BASE_SUCCESS_RATE", 0.5)

        # 境界难度影响 - 每升一个境界等级减少1%成功率
        realm_difficulty_reduction = BREAKTHROUGH_CONFIG.get("REALM_DIFFICULTY_REDUCTION", 0.01)
        realm_penalty = target_realm * realm_difficulty_reduction

        # 气运影响
        luck_bonus = (character.luck_value - 50) * 0.005  # 气运每点影响0.5%

        # 灵根影响 - 使用constants中定义的灵根系统
        from shared.constants import SPIRITUAL_ROOTS
        spiritual_root_bonus = 0.0

        if character.spiritual_root in SPIRITUAL_ROOTS:
            root_info = SPIRITUAL_ROOTS[character.spiritual_root]
            # 直接使用灵根配置中的突破加成
            spiritual_root_bonus = root_info.get("breakthrough_bonus", 0.0)

        # TODO: 物品加成
        item_bonus = 0.0
        if use_items:
            # 计算辅助物品的成功率加成
            pass

        # 计算最终成功率
        final_rate = base_rate - realm_penalty + luck_bonus + spiritual_root_bonus + item_bonus

        # 限制在0.05-0.95之间（最低5%，最高95%）
        return max(0.05, min(0.95, final_rate))

    @staticmethod
    def calculate_breakthrough_failure_loss_rate(character: Character) -> float:
        """计算突破失败时的修为损失比例"""
        from shared.constants import BREAKTHROUGH_CONFIG, CAVE_SYSTEM_CONFIG

        # 基础损失率20%
        base_loss_rate = BREAKTHROUGH_CONFIG.get("DEFAULT_FAILURE_LOSS_RATE", 0.2)

        # 洞府等级减少损失
        cave_level = character.cave_level
        if "CAVE_UPGRADE" in CAVE_SYSTEM_CONFIG:
            cave_benefits = CAVE_SYSTEM_CONFIG["CAVE_UPGRADE"]["LEVEL_BENEFITS"]
            loss_reduction = cave_benefits.get(cave_level, {}).get("cultivation_loss_reduction", 0)
            actual_loss_rate = max(0, base_loss_rate - loss_reduction)
        else:
            actual_loss_rate = base_loss_rate

        return actual_loss_rate
    
    @staticmethod
    async def can_breakthrough(character: Character, target_realm: int) -> tuple[bool, str]:
        """检查是否可以突破"""
        # 检查目标境界是否有效
        if target_realm <= character.cultivation_realm:
            return False, "目标境界必须高于当前境界"
        
        if target_realm >= len(CULTIVATION_REALMS):
            return False, "目标境界超出范围"
        
        # 检查修为是否足够
        from shared.constants import CULTIVATION_EXP_REQUIREMENTS
        required_exp = CULTIVATION_EXP_REQUIREMENTS.get(target_realm, 0)
        
        if character.cultivation_exp < required_exp:
            return False, f"修为不足，需要{required_exp}点修为"
        
        return True, "可以突破"
