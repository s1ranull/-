import time
import secrets


def _tx(prefix: str) -> str:
    return f"{prefix}_{int(time.time())}_{secrets.token_hex(3)}"


class PaymentAdapter:
    def pay(self, user_id: str, course_id: str, amount: float) -> dict:
        raise NotImplementedError


class StripePaymentAdapter(PaymentAdapter):
    def pay(self, user_id: str, course_id: str, amount: float) -> dict:
        return {
            "provider": "Stripe",
            "status": "success",
            "message": f"Оплата {amount:.2f} выполнена через Stripe",
            "user_id": user_id,
            "course_id": course_id,
            "amount": amount,
            "transaction_id": _tx("stripe"),
            "gateway": "stripe-gateway",
        }


class PayPalPaymentAdapter(PaymentAdapter):
    def pay(self, user_id: str, course_id: str, amount: float) -> dict:
        return {
            "provider": "PayPal",
            "status": "success",
            "message": f"Оплата {amount:.2f} выполнена через PayPal",
            "user_id": user_id,
            "course_id": course_id,
            "amount": amount,
            "transaction_id": _tx("paypal"),
            "gateway": "paypal-checkout",
        }


class LMSAdapter:
    def sync_course(self, user: dict, course: object) -> dict:
        raise NotImplementedError


class MoodleAdapter(LMSAdapter):
    def sync_course(self, user: dict, course: object) -> dict:
        return {
            "provider": "Moodle",
            "status": "success",
            "message": f"Курс '{course.title}' синхронизирован в Moodle для {user['username']}",
            "user_id": user['id'],
            "course_id": course.id,
            "external_ref": _tx("mdl"),
        }


class GoogleClassroomAdapter(LMSAdapter):
    def sync_course(self, user: dict, course: object) -> dict:
        return {
            "provider": "Google Classroom",
            "status": "success",
            "message": f"Курс '{course.title}' синхронизирован в Google Classroom для {user['username']}",
            "user_id": user['id'],
            "course_id": course.id,
            "external_ref": _tx("gclass"),
        }
