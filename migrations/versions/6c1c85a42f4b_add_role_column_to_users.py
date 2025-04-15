"""Add role column to users

Revision ID: 6c1c85a42f4b
Revises: 7241a212ba34
Create Date: 2025-04-11 16:57:53.824141

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = '6c1c85a42f4b'
down_revision: Union[str, None] = '7241a212ba34'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    role_enum = sa.Enum('user', 'admin', name='role')
    role_enum.create(op.get_bind())
    op.add_column('users', sa.Column('role', role_enum, nullable=False, server_default='user'))


def downgrade() -> None:
    op.drop_column('users', 'role')
    sa.Enum(name='role').drop(op.get_bind())
