import json
import logging
from dataclasses import asdict

from bluetape.logging import ContextLogFilter

from .models import PartnerOrderCommand
from .service import OrderIntakeService


def main() -> None:
    logger = logging.Logger("order-intake-example", level=logging.INFO)
    logger.propagate = False
    handler = logging.StreamHandler()
    handler.setLevel(logging.INFO)
    handler.addFilter(ContextLogFilter())
    handler.setFormatter(
        logging.Formatter(
            "%(levelname)s %(message)s request_id=%(request_id)s "
            "partner_id=%(partner_id)s order_id=%(order_id)s"
        )
    )
    logger.addHandler(handler)
    try:
        result = OrderIntakeService(logger).accept(
            PartnerOrderCommand(
                request_id="request-1001",
                partner_id="partner-acme",
                order_id="order-1001",
                sku="SKU-BLUE-42",
                quantity=2,
            )
        )
        print(json.dumps(asdict(result), sort_keys=True))
    finally:
        logger.removeHandler(handler)
        handler.close()


if __name__ == "__main__":
    main()
