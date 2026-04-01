package nusri.fyp.demo.state_machine;

import com.fasterxml.jackson.annotation.JsonProperty;
import lombok.Getter;
import lombok.NoArgsConstructor;
import lombok.Setter;

/**
 * Concrete implementation of action observation, inheriting from {@link AbstractActionObservation}.
 * <br> This class contains the action-object string and the probability, representing the detected "action-object" prediction results.
 * @author Liu Binghong
 * @since 1.0
 */
@Getter
@Setter
@NoArgsConstructor
public final class ActionObservationWithCndctnAchv extends AbstractActionObservation {

    /**
     * The combined description of the action and object being observed.
     * <br> For example, it could be "open door" or "cut paper".
     */
    @JsonProperty("actionAndObject")
    private String actionAndObject;

    /**
     * The probability value of the current action observation.
     * <br> This value typically lies between 0 and 1, representing the confidence in the action-object prediction.
     */
    @JsonProperty("probability")
    private double probability;

    @JsonProperty("achievedCondition")
    private String achievedCondition;

    /**
     * Returns a string representation of the action and object being observed.
     * <br> This method returns the combined action-object string.
     *
     * @return The action-object string, such as "open door" or "cut paper"
     */
    public String s() {
        return this.actionAndObject;
    }

    @Override
    public String toString() {
        return "ActionObservationWithCndctnAchv{" +
                "actionAndObject='" + actionAndObject + '\'' +
                ", probability=" + probability +
                ", achievedCondition='" + achievedCondition + '\'' +
                '}';
    }
}
