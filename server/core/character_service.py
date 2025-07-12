# 角色相关业务逻辑服务

from typing import Optional
from sqlalchemy.ext.asyncio import AsyncSession

from server.database.models import Character
from shared.schemas import CharacterInfo, CharacterAttributes, CharacterTrainingAttributes
from shared.utils import calculate_base_attributes
from shared.constants import CULTIVATION_REALMS


class CharacterService:
    """角色业务逻辑服务"""
    
    @staticmethod
    def build_character_info(character: Character) -> CharacterInfo:
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
        
        # 计算最终属性（基础属性 + 修习属性 + 装备属性）
        final_attributes = CharacterAttributes(
            hp=base_attributes.hp + training_attributes.hp_training,
            physical_attack=base_attributes.physical_attack + training_attributes.physical_attack_training,
            magic_attack=base_attributes.magic_attack + training_attributes.magic_attack_training,
            physical_defense=base_attributes.physical_defense + training_attributes.physical_defense_training,
            magic_defense=base_attributes.magic_defense + training_attributes.magic_defense_training,
            critical_rate=base_attributes.critical_rate,
            critical_damage=base_attributes.critical_damage,
            cultivation_speed=base_attributes.cultivation_speed,
            luck_bonus=base_attributes.luck_bonus
        )
        
        # TODO: 这里将来需要加上装备属性加成
        # if character.equipped_items:
        #     equipment_bonus = calculate_equipment_bonus(character.equipped_items)
        #     final_attributes = add_equipment_bonus(final_attributes, equipment_bonus)
        
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
            equipment=None  # TODO: 将来实现装备信息
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
        # 基础成功率
        base_rate = 0.5
        
        # 气运影响
        luck_bonus = (character.luck_value - 50) * 0.01  # 气运每点影响1%
        
        # 灵根影响
        spiritual_root_bonus = 0.0
        if character.spiritual_root == "天灵根":
            spiritual_root_bonus = 0.3
        elif character.spiritual_root == "变异灵根":
            spiritual_root_bonus = 0.2
        elif character.spiritual_root == "单灵根":
            spiritual_root_bonus = 0.1
        
        # TODO: 物品加成
        item_bonus = 0.0
        if use_items:
            # 计算辅助物品的成功率加成
            pass
        
        # 计算最终成功率
        final_rate = base_rate + luck_bonus + spiritual_root_bonus + item_bonus
        
        # 限制在0-1之间
        return max(0.0, min(1.0, final_rate))
    
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
