# Copyright (c) 2001-2004 Twisted Matrix Laboratories.
# See LICENSE for details.


"""Test cases for Twisted component architecture."""

from zope import interface as zinterface

from twisted.trial import unittest, util
from twisted.python import components
import warnings

compWarn = {'category':components.ComponentsDeprecationWarning}
suppress = [util.suppress(**compWarn)]

# Also filter warnings generated by top-level code
warnings.filterwarnings('ignore', **compWarn)

class IAdder(components.Interface):
    """A sample interface that adds stuff."""

    def add(self, a, b):
        """Returns the sub of a and b."""
        raise NotImplementedError

class ISub(IAdder):
    """Sub-interface."""

class IMultiply(components.Interface):
    """Interface that multiplies stuff."""

    def multiply(self, a, b):
        """Multiply two items."""
        raise NotImplementedError


class IntAdder:
    """Class that implements IAdder interface."""
    
    zinterface.implements(IAdder)

    def add(self, a, b):
        return a + b

class Sub:
    """Class that implements ISub."""

    zinterface.implements(ISub)

    def add(self, a, b):
        return 3


class IntMultiplyWithAdder:
    """Multiply, using Adder object."""

    zinterface.implements(IMultiply)

    def __init__(self, adder):
        self.adder = adder

    def multiply(self, a, b):
        result = 0
        for i in range(a):
            result = self.adder.add(result, b)
        return result

components.registerAdapter(IntMultiplyWithAdder, IntAdder, IMultiply)

class MultiplyAndAdd:
    """Multiply and add."""

    zinterface.implements(IAdder, IMultiply)

    def add(self, a, b):
        return a + b

    def multiply(self, a, b):
        return a * b

class IFoo(ISub):
    pass

class FooAdapterForMAA:

    zinterface.implements(IFoo)

    def __init__(self, instance):
        self.instance = instance

    def add(self, a, b):
        return self.instance.add(a, b)

components.registerAdapter(FooAdapterForMAA, MultiplyAndAdd, IFoo)


class InterfacesTestCase(unittest.TestCase):
    """Test interfaces."""

    def testModules(self):
        self.assertEquals(components.Interface.__module__, "twisted.python.components")
        self.assertEquals(IAdder.__module__, "twisted.test.test_components")
        self.assertEquals(IFoo.__module__, "twisted.test.test_components")
    
    def testClasses(self):
        components.fixClassImplements(Sub)
        components.fixClassImplements(MultiplyAndAdd)
        self.assert_( IMultiply.implementedBy(MultiplyAndAdd) )
        self.assert_( IAdder.implementedBy(MultiplyAndAdd) )
        self.assert_( IAdder.implementedBy(Sub) )
        self.assert_( ISub.implementedBy(Sub) )

    def testInstances(self):
        o = MultiplyAndAdd()
        self.assert_( IMultiply.providedBy(o) )
        self.assert_( IMultiply.providedBy(o) )

        o = Sub()
        self.assert_( IAdder.providedBy(o) )
        self.assert_( ISub.providedBy(o) )

    def testOther(self):
        self.assert_( not ISub.providedBy(3) )
        self.assert_( not ISub.providedBy("foo") )


class Compo(components.Componentized):
    num = 0
    def inc(self):
        self.num = self.num + 1
        return self.num

class IAdept(components.Interface):
    def adaptorFunc(self):
        raise NotImplementedError()

class IElapsed(components.Interface):
    def elapsedFunc(self):
        """
        1!
        """

class Adept(components.Adapter):
    zinterface.implements(IAdept)
    def __init__(self, orig):
        self.original = orig
        self.num = 0
    def adaptorFunc(self):
        self.num = self.num + 1
        return self.num, self.original.inc()

class Elapsed(components.Adapter):
    zinterface.implements(IElapsed)
    def elapsedFunc(self):
        return 1

components.registerAdapter(Adept, Compo, IAdept)
components.registerAdapter(Elapsed, Compo, IElapsed)

class AComp(components.Componentized):
    pass
class BComp(AComp):
    pass
class CComp(BComp):
    pass

class ITest(components.Interface):
    pass
class ITest2(components.Interface):
    pass
class ITest3(components.Interface):
    pass
class ITest4(components.Interface):
    pass
class Test(components.Adapter):
    zinterface.implements(ITest, ITest3, ITest4)
    def __init__(self, orig):
        pass
class Test2:
    zinterface.implements(ITest2)
    temporaryAdapter = 1
    def __init__(self, orig):
        pass

components.registerAdapter(Test, AComp, ITest)
components.registerAdapter(Test, AComp, ITest3)
components.registerAdapter(Test2, AComp, ITest2)




class ComponentizedTestCase(unittest.TestCase):
    """Simple test case for caching in Componentized.
    """
    def testComponentized(self):
        c = Compo()
        assert c.getComponent(IAdept).adaptorFunc() == (1, 1)
        assert c.getComponent(IAdept).adaptorFunc() == (2, 2)
        assert IElapsed(IAdept(c)).elapsedFunc() == 1

    def testInheritanceAdaptation(self):
        c = CComp()
        co1 = c.getComponent(ITest)
        co2 = c.getComponent(ITest)
        co3 = c.getComponent(ITest2)
        co4 = c.getComponent(ITest2)
        assert co1 is co2
        assert co3 is not co4
        c.removeComponent(co1)
        co5 = c.getComponent(ITest)
        co6 = c.getComponent(ITest)
        assert co5 is co6
        assert co1 is not co5

    def testMultiAdapter(self):
        c = CComp()
        co1 = c.getComponent(ITest)
        co2 = c.getComponent(ITest2)
        co3 = c.getComponent(ITest3)
        co4 = c.getComponent(ITest4)
        assert co4 == None
        assert co1 is co3

class AdapterTestCase(unittest.TestCase):
    """Test adapters."""

    def testNoAdapter(self):
        o = Sub()
        multiplier = IMultiply(o, None)
        self.assertEquals(multiplier, None)

    def testSelfIsAdapter(self):
        o = IntAdder()
        adder = IAdder(o, None)
        self.assert_( o is adder )

    def testGetAdapter(self):
        o = IntAdder()
        self.assertEquals(o.add(3, 4), 7)

        # get an object implementing IMultiply
        multiplier = IMultiply(o, None)

        # check that it complies with the IMultiply interface
        self.assertEquals(multiplier.multiply(3, 4), 12)

    def testGetAdapterClass(self):
        mklass = components.getAdapterClass(IntAdder, IMultiply, None)
        self.assertEquals(mklass, IntMultiplyWithAdder)

    def testGetSubAdapter(self):
        o = MultiplyAndAdd()
        self.assert_( not IFoo.providedBy(o) )
        foo = IFoo(o, None)
        self.assert_( isinstance(foo, FooAdapterForMAA) )

    def testParentInterface(self):
        o = Sub()
        adder = IAdder(o, None)
        self.assertIdentical(o, adder)

    def testBadRegister(self):
        # should fail because we already registered an IMultiply adapter for IntAdder
        self.assertRaises(ValueError, components.registerAdapter, IntMultiplyWithAdder, IntAdder, IMultiply)
    
    def testAllowDuplicates(self):
        components.ALLOW_DUPLICATES = 1
        try: 
            components.registerAdapter(IntMultiplyWithAdder, IntAdder,
                                       IMultiply)
        except ValueError:
            self.fail("Should have allowed re-registration")
            
        # should fail because we already registered an IMultiply adapter
        # for IntAdder
        components.ALLOW_DUPLICATES = 0
        self.assertRaises(ValueError, components.registerAdapter,
                          IntMultiplyWithAdder, IntAdder, IMultiply)
    
    def testAdapterGetComponent(self):
        o = object()
        a = Adept(o)
        self.assertRaises(components.CannotAdapt, IAdder, a)
        self.assertEquals(IAdder(a, default=None), None)

    def testMultipleInterfaceRegistration(self):
        class IMIFoo(components.Interface):
            pass
        class IMIBar(components.Interface):
            pass
        class MIFooer(components.Adapter):
            zinterface.implements(IMIFoo, IMIBar)
        class Blegh:
            pass
        components.registerAdapter(MIFooer, Blegh, IMIFoo, IMIBar)
        self.assert_(isinstance(IMIFoo(Blegh()), MIFooer))
        self.assert_(isinstance(IMIBar(Blegh()), MIFooer))

class IMeta(components.Interface):
    pass

class MetaAdder(components.Adapter):
    zinterface.implements(IMeta)
    def add(self, num):
        return self.original.num + num

class BackwardsAdder(components.Adapter):
    zinterface.implements(IMeta)
    def add(self, num):
        return self.original.num - num

class MetaNumber:
    def __init__(self, num):
        self.num = num

class FakeAdder:
    def add(self, num):
        return num + 5

class FakeNumber:
    num = 3

class ComponentNumber(components.Componentized):
    def __init__(self):
        self.num = 0
        components.Componentized.__init__(self)

class ComponentMeta(components.Adapter):
    zinterface.implements(IMeta)
    def __init__(self, original):
        components.Adapter.__init__(self, original)
        self.num = self.original.num

class ComponentAdder(ComponentMeta):
    def add(self, num):
        self.num += num
        return self.num

class ComponentDoubler(ComponentMeta):
    def add(self, num):
        self.num += (num * 2)
        return self.original.num

components.registerAdapter(MetaAdder, MetaNumber, IMeta)
components.registerAdapter(ComponentAdder, ComponentNumber, IMeta)

class IAttrX(components.Interface):
    def x(self):
        pass

class IAttrXX(components.Interface):
    def xx(self):
        pass

class Xcellent:
    zinterface.implements(IAttrX)
    def x(self):
        return 'x!'

class DoubleXAdapter:
    num = 42
    def __init__(self, original):
        self.original = original
    def xx(self):
        return (self.original.x(), self.original.x())
    def __cmp__(self, other):
        return cmp(self.num, other.num)

components.registerAdapter(DoubleXAdapter, IAttrX, IAttrXX)

class TestMetaInterface(unittest.TestCase):
    
    def testBasic(self):
        n = MetaNumber(1)
        self.assertEquals(IMeta(n).add(1), 2)

    def testComponentizedInteraction(self):
        c = ComponentNumber()
        IMeta(c).add(1)
        IMeta(c).add(1)
        self.assertEquals(IMeta(c).add(1), 3)

    def testAdapterWithCmp(self):
        # Make sure that a __cmp__ on an adapter doesn't break anything
        xx = IAttrXX(Xcellent())
        self.assertEqual(('x!', 'x!'), xx.xx())


class IISource1(components.Interface): pass
class IISource2(components.Interface): pass
class IIDest1(components.Interface): pass

class Dest1Impl(components.Adapter):
    zinterface.implements(IIDest1)

class Dest1Impl2(components.Adapter):
    zinterface.implements(IIDest1)

class Source12:
    zinterface.implements(IISource1, IISource2)

class Source21:
    zinterface.implements(IISource2, IISource1)

components.registerAdapter(Dest1Impl, IISource1, IIDest1)
components.registerAdapter(Dest1Impl2, IISource2, IIDest1)

class TestInterfaceInterface(unittest.TestCase):

    def testBasic(self):
        s12 = Source12()
        d = IIDest1(s12)
        self.failUnless(isinstance(d, Dest1Impl), str(s12))
        s21 = Source21()
        d = IIDest1(s21)
        self.failUnless(isinstance(d, Dest1Impl2), str(s21))


class IZope(zinterface.Interface):
    def amethod(a, b):
        pass

class Zopeable:
    pass

components.registerAdapter(lambda o: id(o), Zopeable, IZope)

class TestZope(unittest.TestCase):

    def testAdapter(self):
        x = Zopeable()
        self.assertEquals(id(x), IZope(x))

    def testSignatureString(self):
        # Make sure it cuts off the self from old t.p.c signatures.
        self.assertEquals(IAdder['add'].getSignatureString(), "(a, b)")
        self.assertEquals(IZope['amethod'].getSignatureString(), "(a, b)")

    def testClassIsGCd(self):
        import weakref, gc
        class Test(object):
            zinterface.implements(IZope)
        # Do some stuff with it
        components.backwardsCompatImplements(Test)
        IZope(Test())

        # Make a weakref to it, then ensure the weakref goes away
        r = weakref.ref(Test)
        del Test
        gc.collect()
        self.assertEquals(r(), None)
        
warnings.filterwarnings('default', **compWarn)
