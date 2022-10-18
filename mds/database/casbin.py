import casbin
import casbin_sqlalchemy_adapter

adapter = casbin_sqlalchemy_adapter.Adapter('sqlite:///casbin.db')
casbinEnforcer = casbin.Enforcer('./tests/model.conf', adapter)