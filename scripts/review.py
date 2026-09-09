import random
from datetime import datetime, timezone

from sqlalchemy import select

from app.database import SessionLocal
from app.models import AnswerComparison


def main() -> None:
    db = SessionLocal()
    rows = db.scalars(
        select(AnswerComparison)
        .where(AnswerComparison.preferred.is_(None))
        .order_by(AnswerComparison.created_at)
    ).all()

    print(f'{len(rows)} pairs to review.\n')

    for row in rows:
        flipped = random.random() < 0.5
        left, right = (
            (row.answer_b, row.answer_a) if flipped else (row.answer_a, row.answer_b)
        )

        print('=' * 70)
        print(f'Q: {row.question}')
        print(f'(best retrieval distance: {row.best_distance:.3f})')
        print(f'--- LEFT ---\n{left}\n')
        print(f'--- RIGHT ---\n{right}\n')

        choice = input('left / right / tie / bad / skip / quit > ').strip().lower()

        match choice:
            case 'quit':
                break
            case 'skip':
                continue

            case 'left':
                row.preferred = 'b' if flipped else 'a'
            case 'right':
                row.preferred = 'a' if flipped else 'b'
            case 'tie':
                row.preferred = 'tie'
            case 'bad':
                row.preferred = 'both'
            case _:
                continue

        note = input('not (enter to skip) > ').strip()
        row.note = note or None
        row.reviewed_at = datetime.now(timezone.utc)
        db.commit()

    db.close()


if __name__ == '__main__':
    main()
