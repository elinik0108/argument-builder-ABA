import sys
from itertools import product


# Load the moderation knowledge base

def parser(path):
    assumptions = set()
    contrary = {}
    rules = []

    for line in open(path):

        ## Put all assumptions into the set
        if line.startswith("assumption "):
            name = line[len("assumption "):].strip()
            assumptions.add(name)

        ## Put all contraries into the dictionary
        elif line.startswith("contrary(") and "=" in line:
            default = line[line.index("(") + 1: line.index(")")].strip()
            overturner = line.split("=", 1)[1].strip()
            contrary[default] = overturner

        ## Put all rules into the rule list
        elif ":-" in line:
            claim_part, body_part = line.split(":-", 1)
            claim = claim_part.strip()
            body_part = body_part.strip().rstrip(".")

            parts = body_part.split(",")
            body = []
            for p in parts:
                p = p.strip()
                if p != "":
                    body.append(p)

            rules.append((claim, body))

    ## Every assumption should have a contrary
    for a in assumptions:
        if a not in contrary:
            raise ValueError("Default '" + a + "' has no declared contrary.")

    return assumptions, contrary, rules



def build_argument(claim, assumptions, rules):
    found = []

    ## case 1: A claim that is a default assumption supports itself
    if claim in assumptions:
        found.append(((claim,), claim))

    ## Otherwise look for rules that conclude this claim
    for pol_claim, body in rules:
        if pol_claim != claim:
            continue

        ## case 2
        ## rule with empty body is fact
        if not body:
            found.append(((), claim))
            continue

        ## case 3
        ## Recursive loop to find bodies that has arguments to back it up
        sub_args_per_body = []
        for p in body:
            sub_args_per_body.append(build_argument(p, assumptions, rules))

        # If any body has no supporting argument, this rule can't fire
        skip = False
        for s in sub_args_per_body:
            if len(s) == 0:
                skip = True
                break

        if skip:
            continue

        ## Support of an argument is the combination of all sub-arguments that argument rely on
        for combo in product(*sub_args_per_body):
            combined_support = set()
            for (sub_support, _) in combo:
                combined_support.update(sub_support)
            found.append((tuple(sorted(combined_support)), claim))

    ## Arguments with same support and claim are the same,
    ## Removing duplicated arguments with same claim and support
    unique = []
    for arg in found:
        if arg not in unique:
            unique.append(arg)
    return unique


def build_all_arguments(assumptions, contrary, rules):
    ## Put all atoms that is in the knowledge base
    atoms = set(assumptions)
    atoms.update(contrary.values())
    for claim, body in rules:
        atoms.add(claim)
        atoms.update(body)

    all_args = []
    for atom in atoms:
        for arg in build_argument(atom, assumptions, rules):
            if arg not in all_args:
                all_args.append(arg)
    return all_args


# Finding defeats between moderation arguments

def find_defeats(moderation_arguments, contrary):
    defeats = []
    for attacker in moderation_arguments:
        _, attacker_verdict = attacker
        for target in moderation_arguments:
            target_support, _ = target
            for default in target_support:
                if default in contrary and attacker_verdict == contrary[default]:
                    defeats.append((attacker, target))
                    break
    return defeats


def format_argument(arg):
    support, claim = arg
    if support:
        return "(" + ", ".join(support) + " |- " + claim + ")"
    else:
        return "( |- " + claim + ")"


def analyze_cases(path):
    assumptions, contrary, rules = parser(path)

    print("Assumptions:", sorted(assumptions))
    print("Contraries: ", contrary)
    print()
    print("rules: ")
    for claim, body in rules:
        if body:
            print(claim + " :- " + ", ".join(body))
        else:
            print(claim + " :- ")

    args = build_all_arguments(assumptions, contrary, rules)
    args = sorted(args, key=lambda x: (x[1], x[0]))
    ids = {}
    for i, arg in enumerate(args, start=1):
        ids[arg] = "A" + str(i)

    print()
    print("Arguments: " + str(len(args)))
    for arg in args:
        print(ids[arg] + ": " + format_argument(arg))

    # find defeats
    defeats = find_defeats(args, contrary)
    print()
    print("Defeats: " + str(len(defeats)))
    if not defeats:
        print("No defeats.)")
    for attacker, target in defeats:
        target_support, _ = target
        _, attacker_verdict = attacker
        defeated_default = None
        for default in target_support:
            if default in contrary and contrary[default] == attacker_verdict:
                defeated_default = default
                break
        print(ids[attacker] + " defeats " + ids[target])

## Main function
if __name__ == "__main__":
    if len(sys.argv) != 2:
        print("Error: Include the knowledge base file as argument.")
        sys.exit(1)
    analyze_cases(sys.argv[1])