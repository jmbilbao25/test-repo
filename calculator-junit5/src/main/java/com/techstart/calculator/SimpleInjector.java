package com.techstart.calculator;

import java.lang.reflect.Constructor;
import java.lang.reflect.InvocationTargetException;
import java.util.HashMap;
import java.util.LinkedHashSet;
import java.util.Map;
import java.util.Set;

import jakarta.inject.Inject;

/**
 * A dependency injection container in about eighty lines.
 *
 * <p>The assignment allows either a framework or a simple injector, and this
 * project has both so the write-up can compare them. What this class shows is
 * that the idea is small: keep a map from interface to implementation, find the
 * constructor to call, resolve each of its parameters the same way, and cache
 * the result if the type is a singleton.
 *
 * <p>What it does not do is the reason Guice is still worth having. There is no
 * field or method injection, no scopes beyond singleton, no qualifiers so a type
 * can only be bound once, no provider indirection, no interception, and the
 * cycle detection below reports a problem rather than resolving it.
 */
public class SimpleInjector {

    private final Map<Class<?>, Class<?>> bindings = new HashMap<>();
    private final Map<Class<?>, Object> singletons = new HashMap<>();

    /** Records that requests for {@code contract} should be satisfied by {@code implementation}. */
    public <T> SimpleInjector bind(Class<T> contract, Class<? extends T> implementation) {
        bindings.put(contract, implementation);
        return this;
    }

    /** Supplies a ready-made object, so a test can inject something it built itself. */
    public <T> SimpleInjector bindInstance(Class<T> contract, T instance) {
        singletons.put(contract, instance);
        return this;
    }

    public <T> T get(Class<T> requested) {
        return resolve(requested, new LinkedHashSet<>());
    }

    private <T> T resolve(Class<T> requested, Set<Class<?>> inProgress) {
        Object existing = singletons.get(requested);
        if (existing != null) {
            return requested.cast(existing);
        }

        Class<?> target = bindings.getOrDefault(requested, requested);

        if (target.isInterface()) {
            throw new IllegalStateException("no binding for " + target.getName());
        }
        if (!inProgress.add(target)) {
            throw new IllegalStateException("dependency cycle: " + describe(inProgress, target));
        }

        Constructor<?> constructor = chooseConstructor(target);
        Object[] arguments = new Object[constructor.getParameterCount()];
        Class<?>[] parameterTypes = constructor.getParameterTypes();
        for (int i = 0; i < arguments.length; i++) {
            arguments[i] = resolve(parameterTypes[i], inProgress);
        }

        Object created;
        try {
            constructor.setAccessible(true);
            created = constructor.newInstance(arguments);
        } catch (InstantiationException | IllegalAccessException e) {
            throw new IllegalStateException("could not construct " + target.getName(), e);
        } catch (InvocationTargetException e) {
            // Surface what the constructor threw, not the reflection wrapper.
            throw new IllegalStateException(
                    target.getSimpleName() + " constructor failed", e.getCause());
        }

        inProgress.remove(target);

        if (target.isAnnotationPresent(jakarta.inject.Singleton.class)) {
            singletons.put(requested, created);
            singletons.put(target, created);
        }
        return requested.cast(created);
    }

    /**
     * The constructor annotated {@code @Inject}, or the only one there is.
     *
     * <p>Being strict here is deliberate. Guessing at the longest constructor
     * is how a container ends up doing something the author did not intend, and
     * a clear failure at wiring time is cheaper than a puzzling object later.
     */
    private static Constructor<?> chooseConstructor(Class<?> target) {
        Constructor<?>[] all = target.getDeclaredConstructors();
        Constructor<?> annotated = null;
        for (Constructor<?> candidate : all) {
            if (candidate.isAnnotationPresent(Inject.class)) {
                if (annotated != null) {
                    throw new IllegalStateException(
                            target.getName() + " has more than one @Inject constructor");
                }
                annotated = candidate;
            }
        }
        if (annotated != null) {
            return annotated;
        }
        if (all.length == 1) {
            return all[0];
        }
        throw new IllegalStateException(
                target.getName() + " has " + all.length
                        + " constructors and none is annotated @Inject");
    }

    private static String describe(Set<Class<?>> inProgress, Class<?> repeated) {
        StringBuilder chain = new StringBuilder();
        for (Class<?> type : inProgress) {
            chain.append(type.getSimpleName()).append(" -> ");
        }
        return chain.append(repeated.getSimpleName()).toString();
    }

    /** The wiring from {@link CalculatorModule}, expressed for this injector. */
    public static SimpleInjector withDefaults() {
        return new SimpleInjector()
                .bind(RoundingPolicy.class, BankersRoundingPolicy.class)
                .bind(OperationLog.class, InMemoryOperationLog.class);
    }
}
