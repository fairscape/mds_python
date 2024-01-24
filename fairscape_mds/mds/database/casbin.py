import casbin
import casbin_sqlalchemy_adapter

adapter = casbin_sqlalchemy_adapter.Adapter('sqlite:///casbin.db')
casbinEnforcer = casbin.Enforcer('./mds/database/default_model.conf', adapter)