class DifficultyStrategy:
    name = "Unknown"

    def get_message(self) -> str:
        raise NotImplementedError


class BeginnerStrategy(DifficultyStrategy):
    name = "Beginner"

    def get_message(self) -> str:
        return "Начальный уровень: показывать более простые вопросы"


class IntermediateStrategy(DifficultyStrategy):
    name = "Intermediate"

    def get_message(self) -> str:
        return "Средний уровень: стандартная сложность"


class AdvancedStrategy(DifficultyStrategy):
    name = "Advanced"

    def get_message(self) -> str:
        return "Продвинутый уровень: показывать более сложные вопросы"


class DifficultyContext:
    @staticmethod
    def choose(avg_percent):
        if avg_percent is None:
            return BeginnerStrategy()
        if avg_percent < 50:
            return BeginnerStrategy()
        if avg_percent < 80:
            return IntermediateStrategy()
        return AdvancedStrategy()
